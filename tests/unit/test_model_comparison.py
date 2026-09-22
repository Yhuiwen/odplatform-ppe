import copy

import pytest

from services.model_comparison_service import replay_comparison, summarize_comparison
from services.val_service import CLASS_NAMES, dump_json, select_checkpoint, sha256
from utils.evaluation_metrics import calculate_metrics


def save_run(path, role, *, change=None):
    path.mkdir()
    boxes = [{'class_id': i, 'box': [0.1, 0.1, 0.15, 0.15]} for i in range(7)]
    config = {'checkpoint_role': role, 'evaluation_id': role, 'output_path': str(path),
              'split': 'test', 'operating_confidence': 0.25, 'matching_iou': 0.5,
              'small_object_area': 0.01, 'imgsz': 640}
    raw = {'evaluation_config': config, 'class_names': CLASS_NAMES,
           'records': [{'image': 'test/images/synthetic.png', 'image_sha256': 'synthetic-image',
                        'label_sha256': 'synthetic-label', 'width': 32, 'height': 32,
                        'truth': boxes, 'predictions': [dict(b, confidence=0.9) for b in boxes
                                                      if role == 'best' or b['class_id'] != 2]}]}
    record = {'status': 'COMPLETED', 'config': copy.deepcopy(config),
              'integrity_unchanged': True, 'split': 'test', 'checkpoint_sha256': role,
              'implementation_sha256': {'metric.py': 'synthetic-code'},
              'runtime': {'fixture': True}, 'python': 'fixture', 'platform': 'fixture',
              'duration_seconds': 0}
    if change:
        change(record, raw)
    dump_json(path / 'predictions.json', raw)
    dump_json(path / 'dataset_before.json', {'synthetic-image': 'unchanged'})
    dump_json(path / 'metrics.json', calculate_metrics(raw['records'], raw['class_names']))
    record['artifact_sha256'] = {p.name: sha256(p) for p in path.iterdir()}
    dump_json(path / 'run_record.json', record)


def test_checkpoint_comparison_replays_and_reports_recall_tradeoff(tmp_path):
    save_run(tmp_path / 'best', 'best')
    save_run(tmp_path / 'last', 'last')
    result = summarize_comparison(tmp_path)
    assert result['conditions_equal']
    assert result['last_minus_best']['no_hardhat_recall'] == -1
    assert result['last_minus_best']['no_vest_recall'] == 0
    assert result['last_minus_best']['small_object_recall'] == pytest.approx(-1 / 7)
    assert result['results'][0]['overall']['recall'] == 1
    assert len(result['results'][1]['per_class']) == 7
    dump_json(tmp_path / 'comparison.json', result)
    assert replay_comparison(tmp_path) == result
    result['last_minus_best']['recall'] = 123
    dump_json(tmp_path / 'comparison.json', result)
    with pytest.raises(ValueError, match='retained'):
        replay_comparison(tmp_path)


@pytest.mark.parametrize('field', ['protocol', 'test_records', 'runtime', 'implementation'])
def test_different_comparison_conditions_rejected(tmp_path, field):
    save_run(tmp_path / 'best', 'best')
    def change(record, raw):
        if field == 'protocol':
            raw['evaluation_config']['imgsz'] = 320
            record['config']['imgsz'] = 320
        elif field == 'test_records':
            raw['records'][0]['image_sha256'] = 'different-image'
        elif field == 'runtime':
            record['runtime'] = {'fixture': 'different'}
        else:
            record['implementation_sha256'] = {'metric.py': 'different-code'}
    save_run(tmp_path / 'last', 'last', change=change)
    with pytest.raises(ValueError, match=f'conditions differ: {field}'):
        summarize_comparison(tmp_path)


def test_same_checkpoint_not_claimed_as_distinct_models(tmp_path):
    save_run(tmp_path / 'best', 'best')
    save_run(tmp_path / 'last', 'last', change=lambda r, _: r.update(checkpoint_sha256='best'))
    with pytest.raises(ValueError, match='distinct checkpoint'):
        summarize_comparison(tmp_path)


def test_checkpoint_selector_requires_frozen_inventory():
    best = {'path': 'models/EXP-001/best.pt', 'sha256': 'best'}
    last = {'path': 'models/EXP-001/last.pt', 'sha256': 'last'}
    manifest = {'best_checkpoint': best, 'artifact_inventory': [last]}
    assert select_checkpoint(manifest, 'best') == best
    assert select_checkpoint(manifest, 'last') == last
    with pytest.raises(ValueError, match='best or last'):
        select_checkpoint(manifest, '../new.pt')
    with pytest.raises(ValueError, match='uniquely registered'):
        select_checkpoint({'best_checkpoint': best}, 'last')
    with pytest.raises(ValueError, match='uniquely registered'):
        select_checkpoint(dict(manifest, artifact_inventory=[last, last]), 'last')
