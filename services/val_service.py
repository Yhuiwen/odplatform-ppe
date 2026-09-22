"""Read-only EXP-001 evaluation with immutable-input and replay checks."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable

import yaml
from PIL import Image

from utils.evaluation_metrics import IOU_THRESHOLDS, calculate_metrics, iou, match_boxes
from utils.paths import PROJECT_ROOT

CLASS_NAMES = ['person', 'hardhat', 'no_hardhat', 'vest', 'no_vest', 'machinery', 'vehicle']


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def dump_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def tree_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(root.rglob('*')) if p.is_file()}


def verify_manifest(root: Path, expected: str) -> None:
    manifest = root / 'metadata/checksums.sha256'
    if sha256(manifest) != expected:
        raise ValueError('Processed manifest identity mismatch')
    for line in manifest.read_text(encoding='utf-8').splitlines():
        digest, relative = line.split('  ', 1)
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256(path) != digest:
            raise ValueError(f'Dataset manifest mismatch: {relative}')


def read_truth(path: Path) -> list[dict]:
    result = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f'Invalid label: {path}')
        cid = int(fields[0])
        x, y, w, h = map(float, fields[1:])
        result.append({'class_id': cid, 'box': [x - w / 2, y - h / 2, x + w / 2, y + h / 2]})
    return result


def select_checkpoint(manifest: dict, role: str) -> dict:
    """Select only the best or last checkpoint already frozen in Phase 2."""
    if role == 'best':
        return manifest['best_checkpoint']
    if role != 'last':
        raise ValueError('Checkpoint role must be best or last')
    expected = (Path(manifest['best_checkpoint']['path']).parent / 'last.pt').as_posix()
    matches = [item for item in manifest.get('artifact_inventory', []) if item['path'] == expected]
    if len(matches) != 1:
        raise ValueError('Last checkpoint must be uniquely registered in frozen inventory')
    return matches[0]


def replay(directory: str | Path) -> dict:
    """Recompute all metrics from retained predictions without loading a model."""
    directory = Path(directory)
    record = json.loads((directory / 'run_record.json').read_text(encoding='utf-8'))
    if record['status'] != 'COMPLETED':
        raise ValueError('Cannot replay an incomplete run')
    for filename, digest in record['artifact_sha256'].items():
        path = (directory / filename).resolve()
        if not path.is_relative_to(directory.resolve()) or sha256(path) != digest:
            raise ValueError(f'Artifact checksum mismatch: {filename}')
    raw = json.loads((directory / 'predictions.json').read_text(encoding='utf-8'))
    config = raw['evaluation_config']
    calculated = calculate_metrics(raw['records'], raw['class_names'],
                                   confidence=config['operating_confidence'],
                                   matching_iou=config['matching_iou'],
                                   small_area=config['small_object_area'])
    saved = json.loads((directory / 'metrics.json').read_text(encoding='utf-8'))
    if calculated != saved:
        raise ValueError('Replayed metrics differ from retained metrics')
    return calculated


def render_confusion(metrics: dict, directory: Path) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    cm = metrics['confusion_matrix']
    matrix = np.array(cm['counts'])
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix, cmap='Blues')
    ax.set_xticks(range(len(cm['labels'])), cm['labels'], rotation=45, ha='right')
    ax.set_yticks(range(len(cm['labels'])), cm['labels'])
    ax.set_xlabel('True class')
    ax.set_ylabel('Predicted class')
    ax.set_title(f"EXP-001 test | conf {metrics['operating_confidence']} | IoU {metrics['matching_iou']}")
    for (r, c), value in np.ndenumerate(matrix):
        ax.text(c, r, str(value), ha='center', va='center',
                color='white' if value > matrix.max() / 2 else 'black')
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(directory / 'confusion_matrix.png', dpi=160)
    plt.close(fig)


def check_reference_metrics(records: list[dict], metrics: dict) -> dict:
    """Cross-check real saved predictions against the pinned library metrics."""
    from types import SimpleNamespace
    import numpy as np
    import torch
    from ultralytics.engine.validator import BaseValidator
    from ultralytics.utils.metrics import ap_per_class

    reference_tp, confidences, predicted_classes, target_classes = [], [], [], []
    validator = SimpleNamespace(iouv=torch.tensor(IOU_THRESHOLDS, dtype=torch.float64))
    for record in records:
        gt, pred = record['truth'], record['predictions']
        gt_cls = [x['class_id'] for x in gt]
        pred_cls = [x['class_id'] for x in pred]
        overlaps = torch.tensor([[iou(g['box'], p['box']) for p in pred] for g in gt],
                                dtype=torch.float64).reshape(len(gt), len(pred))
        reference = BaseValidator.match_predictions(
            validator, torch.tensor(pred_cls), torch.tensor(gt_cls), overlaps).numpy()
        ours = np.zeros((len(pred), 10), dtype=bool)
        for index, threshold in enumerate(IOU_THRESHOLDS):
            for _, pi, _ in match_boxes(gt, pred, threshold):
                ours[pi, index] = True
        if not np.array_equal(ours, reference):
            raise ValueError(f"Reference matching differs: {record['image']}")
        reference_tp.append(reference)
        confidences.extend(x['confidence'] for x in pred)
        predicted_classes.extend(pred_cls)
        target_classes.extend(gt_cls)
    result = ap_per_class(np.concatenate(reference_tp), np.array(confidences),
                          np.array(predicted_classes), np.array(target_classes), plot=False)
    reference_ap = result[5]
    class_ids = result[6]
    delta = 0.0
    for index, class_id in enumerate(class_ids):
        own = metrics['per_class'][int(class_id)]['AP_by_iou']
        delta = max(delta, float(np.max(np.abs(reference_ap[index] - own))))
    if delta > 1e-10:
        raise ValueError(f'Reference AP differs: max absolute delta {delta}')
    return {'status': 'PASS', 'matching_equal': True, 'AP_max_absolute_delta': delta,
            'reference': 'Ultralytics 8.4.157 BaseValidator.match_predictions + ap_per_class',
            'scope': 'same retained single-label NMS predictions; not a second model run'}


class ValService:
    def evaluate(self, config: dict[str, Any], *, project_root: Path = PROJECT_ROOT,
                 predictor_factory: Callable | None = None) -> dict:
        required = {'evaluation_id', 'experiment_id', 'model_manifest', 'dataset_root', 'split',
                    'expected_images', 'output_path', 'ultralytics_version', 'imgsz', 'device', 'batch',
                    'seed', 'confidence_floor', 'nms_iou', 'max_det', 'operating_confidence',
                    'matching_iou', 'small_object_area', 'half', 'augment', 'agnostic_nms'}
        if required - config.keys():
            raise ValueError(f'Missing evaluation fields: {sorted(required - config.keys())}')
        if config['experiment_id'] != 'EXP-001' or config['split'] != 'test':
            raise ValueError('This pipeline only evaluates EXP-001 on the frozen test split')
        if config['batch'] != 1 or config['augment'] or config['half'] or config['agnostic_nms']:
            raise ValueError('Evaluation requires batch 1, FP32, no TTA, class-aware NMS')
        if not 0 < config['nms_iou'] <= 1 or not 0 < config['matching_iou'] <= 1:
            raise ValueError('Invalid IoU thresholds')
        if type(config['imgsz']) is not int or config['imgsz'] <= 0 or config['max_det'] <= 0:
            raise ValueError('Invalid image size or detection limit')
        if not 0 <= config['confidence_floor'] <= config['operating_confidence'] <= 1:
            raise ValueError('Invalid confidence thresholds')
        project_root = project_root.resolve()
        dataset = (project_root / config['dataset_root']).resolve()
        output = (project_root / config['output_path']).resolve()
        allowed = (project_root / 'artifacts/reports/EXP-001-evaluation').resolve()
        if not output.is_relative_to(allowed) or output == allowed or output.exists():
            raise ValueError('Evaluation output must be a new directory under artifacts/reports/EXP-001-evaluation')
        manifest_path = (project_root / config['model_manifest']).resolve()
        manifest = yaml.safe_load(manifest_path.read_text(encoding='utf-8'))
        if manifest['experiment_id'] != 'EXP-001' or manifest['dataset']['classes'] != CLASS_NAMES:
            raise ValueError('Unexpected model/dataset identity or class order')
        checkpoint_item = select_checkpoint(manifest, config.get('checkpoint_role', 'best'))
        protected = [manifest_path]
        for item in [checkpoint_item, manifest['best_checkpoint'], manifest['configuration'],
                     manifest['dataset']['mapping_contract'], manifest['dataset']['training_contract'],
                     manifest['dataset']['class_mapping'], manifest['dataset']['processed_data_yaml']]:
            path = (project_root / item['path']).resolve()
            if not path.is_file() or sha256(path) != item['sha256']:
                raise ValueError(f"Frozen identity mismatch: {item['path']}")
            protected.append(path)
        if dataset != (project_root / manifest['dataset']['processed_data_yaml']['path']).resolve().parent:
            raise ValueError('Dataset root differs from frozen manifest')
        verify_manifest(dataset, manifest['dataset']['fingerprint']['processed_manifest_sha256'])
        before = tree_hashes(dataset)
        protected_before = {str(p): sha256(p) for p in protected}
        images = sorted((dataset / 'test/images').iterdir())
        labels = sorted((dataset / 'test/labels').glob('*.txt'))
        if len(images) != config['expected_images'] or len(images) != manifest['dataset']['splits']['test']:
            raise ValueError('Test image count differs from frozen split')
        if {p.stem for p in images} != {p.stem for p in labels} or len(images) != len(labels):
            raise ValueError('Test image-label pairing mismatch')
        checkpoint = (project_root / checkpoint_item['path']).resolve()
        output.mkdir(parents=True, exist_ok=False)
        started = time.perf_counter()
        context = {'status': 'STARTED', 'evaluation_id': config['evaluation_id'],
                   'experiment_id': 'EXP-001', 'split': 'test', 'config': config,
                   'started_at_utc': datetime.now(timezone.utc).isoformat(),
                   'checkpoint_sha256': sha256(checkpoint), 'protected_before': protected_before,
                   'dataset_files': len(before), 'python': sys.version, 'platform': platform.platform()}
        context['implementation_sha256'] = {
            p: sha256(PROJECT_ROOT / p) for p in
            ('services/val_service.py', 'utils/evaluation_metrics.py', 'scripts/evaluate.py')
        }
        dump_json(output / 'run_record.json', context)
        dump_json(output / 'dataset_before.json', before)
        try:
            factory = predictor_factory or UltralyticsPredictor
            predictor = factory(checkpoint, config, output)
            if list(predictor.names) != CLASS_NAMES:
                raise ValueError('Checkpoint class order mismatch')
            records = []
            for index, path in enumerate(images):
                label = dataset / 'test/labels' / (path.stem + '.txt')
                with Image.open(path) as opened:
                    image = opened.convert('RGB')
                    predictions = predictor(image)
                    width, height = image.size
                records.append({'image': path.relative_to(dataset).as_posix(),
                                'image_sha256': sha256(path), 'label_sha256': sha256(label),
                                'width': width, 'height': height,
                                'truth': read_truth(label), 'predictions': predictions})
                print(f'Evaluated {index + 1}/{len(images)}', flush=True)
            raw = {'class_names': CLASS_NAMES, 'evaluation_config': config, 'records': records}
            dump_json(output / 'predictions.json', raw)
            metrics = calculate_metrics(records, CLASS_NAMES, confidence=config['operating_confidence'],
                                        matching_iou=config['matching_iou'], small_area=config['small_object_area'])
            if predictor_factory is None:
                context['reference_metric_check'] = check_reference_metrics(records, metrics)
            dump_json(output / 'metrics.json', metrics)
            dump_json(output / 'confusion_matrix.json', metrics['confusion_matrix'])
            dump_json(output / 'error_analysis.json', {k: metrics[k] for k in
                      ('error_counts', 'errors', 'per_image', 'small_object_recall')})
            render_confusion(metrics, output)
            context['runtime'] = predictor.runtime
            context['status'] = 'COMPLETED'
        except Exception as exc:
            context['status'] = 'FAILED'
            context['error'] = f'{type(exc).__name__}: {exc}'
            raise
        finally:
            after = tree_hashes(dataset)
            intact = before == after and all(sha256(Path(p)) == h for p, h in protected_before.items())
            context['integrity_unchanged'] = intact
            context['duration_seconds'] = time.perf_counter() - started
            context['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
            context['artifact_sha256'] = {p.name: sha256(p) for p in output.iterdir()
                                          if p.is_file() and p.name != 'run_record.json'}
            if not intact:
                context['status'] = 'FAILED_INTEGRITY'
            dump_json(output / 'run_record.json', context)
            if not intact:
                raise RuntimeError('Evaluation changed protected files; outputs are not accepted')
        replay(output)
        return {'output_path': str(output), 'metrics': metrics, 'run_record': context}


class UltralyticsPredictor:
    def __init__(self, checkpoint: Path, config: dict, output: Path):
        os.environ['YOLO_CONFIG_DIR'] = str(output / 'ultralytics_settings')
        os.environ['YOLO_AUTOINSTALL'] = 'false'
        import torch
        import ultralytics
        from ultralytics import YOLO
        if ultralytics.__version__ != str(config['ultralytics_version']):
            raise RuntimeError('Ultralytics version differs from evaluation config')
        torch.manual_seed(config['seed'])
        torch.set_num_threads(4)
        torch.use_deterministic_algorithms(True)
        self.model = YOLO(str(checkpoint), task='detect')
        self.names = [self.model.names[i] for i in range(len(self.model.names))]
        self.config, self.output = config, output
        self.runtime = {'torch': torch.__version__, 'ultralytics': ultralytics.__version__,
                        'device': config['device'], 'threads': 4,
                        'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}}

    def __call__(self, image: Image.Image) -> list[dict]:
        c = self.config
        result = self.model.predict(image, imgsz=c['imgsz'], conf=c['confidence_floor'],
                                    iou=c['nms_iou'], max_det=c['max_det'], device=c['device'],
                                    half=False, augment=False, agnostic_nms=False,
                                    rect=False, save=False, save_txt=False, verbose=False,
                                    project=str(self.output), name='inference', exist_ok=True)[0]
        return [{'class_id': int(cid), 'confidence': float(conf), 'box': [float(x) for x in box]}
                for cid, conf, box in zip(result.boxes.cls.cpu().tolist(),
                                         result.boxes.conf.cpu().tolist(), result.boxes.xyxyn.cpu().tolist())]
