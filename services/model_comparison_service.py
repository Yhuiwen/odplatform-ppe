"""Controlled comparison of two frozen checkpoints using the existing evaluator."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from services.val_service import CLASS_NAMES, ValService, dump_json, replay, sha256, select_checkpoint
from utils.paths import PROJECT_ROOT


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def protocol(config: dict) -> dict:
    return {k: v for k, v in config.items() if k not in
            ('evaluation_id', 'output_path', 'checkpoint_role')}


def summarize_comparison(directory: Path) -> dict:
    """Replay both runs and reject different data, protocol, runtime or code."""
    results, baseline = [], None
    for role in ('best', 'last'):
        run = directory / role
        metrics = replay(run)
        record = read_json(run / 'run_record.json')
        raw = read_json(run / 'predictions.json')
        if not record.get('integrity_unchanged'):
            raise ValueError('Run input integrity did not pass')
        if record['config'] != raw['evaluation_config'] or record['config'].get('checkpoint_role') != role:
            raise ValueError('Comparison checkpoint role/config mismatch')
        if raw['class_names'] != CLASS_NAMES or record['split'] != 'test':
            raise ValueError('Comparison requires the frozen test classes')
        identity = {
            'protocol': protocol(record['config']),
            'test_records': [{k: r[k] for k in
                              ('image', 'image_sha256', 'label_sha256', 'width', 'height', 'truth')}
                             for r in raw['records']],
            'dataset_before': read_json(run / 'dataset_before.json'),
            'implementation': record['implementation_sha256'],
            'runtime': record['runtime'], 'python': record['python'], 'platform': record['platform'],
        }
        if baseline is None:
            baseline = identity
        else:
            for key in identity:
                if identity[key] != baseline[key]:
                    raise ValueError(f'Comparison conditions differ: {key}')
        by_name = {r['name']: r for r in metrics['per_class']}
        results.append({
            'checkpoint_role': role, 'checkpoint_sha256': record['checkpoint_sha256'],
            'run_record_sha256': sha256(run / 'run_record.json'),
            'artifact_sha256': record['artifact_sha256'],
            'images': metrics['images'], 'instances': metrics['instances'],
            'overall': metrics['overall'], 'ppe_five_classes': metrics['ppe_five_classes'],
            'per_class': metrics['per_class'],
            'no_hardhat_recall': by_name['no_hardhat']['recall'],
            'no_vest_recall': by_name['no_vest']['recall'],
            'small_object_recall': metrics['small_object_recall'],
            'reference_metric_check': record.get('reference_metric_check'),
            'duration_seconds': record['duration_seconds'],
        })
    if results[0]['checkpoint_sha256'] == results[1]['checkpoint_sha256']:
        raise ValueError('Comparison requires two distinct checkpoint hashes')
    return {'schema_version': 'model-comparison-results-v1', 'status': 'COMPLETED',
            'scope': 'EXP-001 best versus last; same training run, not independent models',
            'conditions_equal': True, 'protocol': baseline['protocol'],
            'implementation_sha256': baseline['implementation'],
            'results': results,
            'last_minus_best': {
                **{k: results[1]['overall'][k] - results[0]['overall'][k]
                   for k in results[0]['overall']},
                **{k: results[1][k] - results[0][k]
                   for k in ('no_hardhat_recall', 'no_vest_recall')},
                'small_object_recall': results[1]['small_object_recall']['small']['recall']
                - results[0]['small_object_recall']['small']['recall']}}


def run_comparison(config_path: Path, *, project_root: Path = PROJECT_ROOT) -> dict:
    project_root = project_root.resolve()
    config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    if config['checkpoint_roles'] != ['best', 'last']:
        raise ValueError('Comparison requires best and last in that order')
    base_path = project_root / config['base_config']
    if sha256(base_path) != config['base_config_sha256']:
        raise ValueError('Base evaluation config hash mismatch')
    base = yaml.safe_load(base_path.read_text(encoding='utf-8'))
    manifest_path = project_root / base['model_manifest']
    manifest = yaml.safe_load(manifest_path.read_text(encoding='utf-8'))
    # Verify both candidates before inference; never download or select new weights.
    for role in config['checkpoint_roles']:
        item = select_checkpoint(manifest, role)
        if sha256(project_root / item['path']) != item['sha256']:
            raise ValueError(f'Frozen {role} checkpoint hash mismatch')
    output = (project_root / config['output_path']).resolve()
    allowed = (project_root / 'artifacts/reports/EXP-001-evaluation').resolve()
    if not output.is_relative_to(allowed) or output == allowed or output.exists():
        raise ValueError('Comparison output must be a new evaluation directory')
    protected = {str(p): sha256(p) for p in (config_path, base_path, manifest_path)}
    output.mkdir(parents=True)
    for role in config['checkpoint_roles']:
        candidate = dict(base, checkpoint_role=role,
                         evaluation_id=f"{config['comparison_id']}-{role}",
                         output_path=(output / role).relative_to(project_root).as_posix())
        ValService().evaluate(candidate, project_root=project_root)
    if any(sha256(Path(p)) != h for p, h in protected.items()):
        raise ValueError('Comparison inputs changed during execution')
    summary = summarize_comparison(output)
    summary['comparison_config_sha256'] = protected[str(config_path)]
    summary['comparison_implementation_sha256'] = sha256(Path(__file__))
    dump_json(output / 'comparison.json', summary)
    return summary


def replay_comparison(directory: Path) -> dict:
    saved = read_json(directory / 'comparison.json')
    calculated = summarize_comparison(directory)
    if any(saved[k] != v for k, v in calculated.items()):
        raise ValueError('Comparison differs from retained results')
    return saved
