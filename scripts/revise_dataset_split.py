"""Create a new split revision; never mutate the frozen training dataset."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.dataset_quality_service import DatasetQualityService


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_revision(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists() or destination == source or source in destination.parents:
        raise ValueError('Destination must be a new independent directory')
    service = DatasetQualityService()
    before = service.analyze(source)
    moves = []
    for group in before['leakage']['perceptual_cross_split_groups']:
        if set(group['splits']) != {'valid', 'test'}:
            raise ValueError('Training contamination requires a separate retraining decision')
        for relative in group['paths']:
            if relative.startswith('test/images/'):
                label = 'test/labels/' + Path(relative).stem + '.txt'
                moves.extend([relative, label])
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('metadata'))
    for relative in sorted(set(moves)):
        target = destination / relative.replace('test/', 'valid/', 1)
        if target.exists():
            raise ValueError('Split destination collision')
        (destination / relative).rename(target)
    data = yaml.safe_load((destination / 'data.yaml').read_text(encoding='utf-8'))
    data['path'] = str(destination)
    (destination / 'data.yaml').write_text(yaml.safe_dump(data, sort_keys=False), encoding='utf-8')
    report = service.analyze(destination, dataset_id='CSS-PPE-10-V1-SPLIT-R2')
    if report['leakage']['exact_detected'] or report['leakage']['perceptual_detected']:
        raise ValueError('Revised split still contains detected cross-split candidates')
    after_source = service.analyze(source)
    if before['dataset_hash']['before'] != after_source['dataset_hash']['before']:
        raise ValueError('Frozen source changed')
    metadata = destination / 'metadata'
    metadata.mkdir()
    manifest = {p.relative_to(destination).as_posix(): digest(p) for p in destination.rglob('*') if p.is_file()}
    for path in (source / 'train').rglob('*'):
        if path.is_file():
            assert digest(path) == digest(destination / path.relative_to(source))
    record = {'version':'split-revision-v1', 'source_payload_sha256':before['dataset_hash']['before'],
              'revised_payload_sha256':report['dataset_hash']['before'], 'moves_from_test_to_valid':sorted(set(moves)),
              'train_byte_identical':True, 'reason':'Confirmed neighboring video frames across valid/test',
              'method':'Move test neighbors to validation; never move validation-tuned data into test',
              'remaining_cross_split_candidates':0}
    (metadata / 'revision.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    (metadata / 'checksums.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    service.write_reports(report, json_output_path=metadata / 'quality_report.json',
                          markdown_output_path=Path('docs/reports/phase-09/V1_SPLIT_R2_QUALITY.md'))
    Path('docs/reports/phase-09/V1_SPLIT_R2_REVISION.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='data/processed/css-ppe-10-v1')
    parser.add_argument('--output', default='data/processed/css-ppe-10-v1-split-r2')
    args = parser.parse_args()
    create_revision(args.source, args.output)
