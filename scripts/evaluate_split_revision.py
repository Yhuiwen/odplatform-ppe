"""Supplemental evaluation of unchanged EXP-001 on the revised independent test set."""
import argparse
import json
from pathlib import Path
import sys
import yaml
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.val_service import UltralyticsPredictor, read_truth, sha256, dump_json, render_confusion, check_reference_metrics
from utils.evaluation_metrics import calculate_metrics


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',default='data/processed/css-ppe-10-v1-split-r2')
    parser.add_argument('--output',default='artifacts/reports/V1-split-r2-evaluation')
    args=parser.parse_args()
    dataset=Path(args.dataset).resolve(); output=Path(args.output).resolve()
    revision=json.loads((dataset/'metadata/revision.json').read_text(encoding='utf-8'))
    assert revision['train_byte_identical'] and revision['remaining_cross_split_candidates']==0
    checkpoint=Path('models/checkpoints/EXP-001/best.pt')
    assert sha256(checkpoint)=='1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61'
    config=yaml.safe_load(Path('configs/evaluation/exp001_test.yaml').read_text(encoding='utf-8'))
    config.update(evaluation_id='EVAL-V1-SPLIT-R2',dataset_root=str(dataset),output_path=str(output),expected_images=80)
    output.mkdir(parents=True,exist_ok=False)
    predictor=UltralyticsPredictor(checkpoint,config,output)
    images=sorted((dataset/'test/images').glob('*'))
    assert len(images)==80
    records=[]
    for index,path in enumerate(images):
        label=dataset/'test/labels'/(path.stem+'.txt')
        with Image.open(path) as original:
            image=original.convert('RGB'); predictions=predictor(image)
            width,height=image.size
        records.append({'image':path.relative_to(dataset).as_posix(),'image_sha256':sha256(path),'label_sha256':sha256(label),
                        'width':width,'height':height,'truth':read_truth(label),'predictions':predictions})
        print(f'Evaluated {index+1}/80',flush=True)
    metrics=calculate_metrics(records,predictor.names,confidence=config['operating_confidence'],matching_iou=config['matching_iou'],small_area=config['small_object_area'])
    for record in records:
        assert sha256(dataset/record['image'])==record['image_sha256']
        assert sha256(dataset/'test/labels'/(Path(record['image']).stem+'.txt'))==record['label_sha256']
    reference=check_reference_metrics(records,metrics)
    dump_json(output/'predictions.json',{'class_names':predictor.names,'evaluation_config':config,'records':records})
    dump_json(output/'metrics.json',metrics)
    render_confusion(metrics,output)
    summary={'status':'PASS','images':80,'checkpoint_sha256':sha256(checkpoint),'train_unchanged':True,
             'supplemental_not_retraining':True,'reference_metric_check':reference,'overall':metrics['overall'],'per_class':metrics['per_class']}
    dump_json(output/'summary.json',summary)
    dump_json(Path('docs/reports/phase-09/V1_SPLIT_R2_EVALUATION.json'),summary)
    print(json.dumps(summary['overall']))


if __name__=='__main__': main()
