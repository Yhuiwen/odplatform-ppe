# Reference Assets

## Purpose and Rules

This register records non-open-source, course-provided, teacher-provided, and
external binary assets. These assets are evidence and reference material only;
they do not replace project implementation or locked acceptance criteria.

Rules:

- No registered asset is included in the repository unless explicitly changed
  by a future user-approved ADR.
- Historical values supplied with an asset remain historical metadata. They are
  not project measurements, reproduction results, or current validation results.
- External assets must not override the locked project architecture or classes.
- Secrets, databases, datasets, and model binaries must remain outside Git.

## REF-001: Teacher YOLO Web v3

| Field | Value |
| --- | --- |
| Asset ID | REF-001 |
| Asset Name | Teacher YOLO Web v3 |
| Provider | Teacher / course-provided |
| Original Filename | `yolo_web_v3.zip` |
| SHA-256 | `9baa48341c1ec8fe63a5dafba5b43932ab11852544ac934c078b9defc8716338` |
| Asset Type | Course reference implementation archive |
| License / Permission Status | TO VERIFY; course-provided only; no redistribution permission established |
| Repository Inclusion | NO |
| Purpose | REFERENCE ONLY for studying design and implementation approaches |
| Allowed Usage | Streamlit 页面组织、图片检测页面、视频检测页面、SQLite 历史记录设计、Plotly 数据大屏、LLM 报告流程、DOCX 报告导出思路、模型懒加载思路、配置驱动思想 |
| Forbidden Usage | 整仓复制；直接采用老师 Web 架构替代 ODPlatform-PPE；复制其中真实 API Key；提交 `history.db`；将老师代码声明为自主实现 |
| Known Metadata | ZIP size: 5,198,767 bytes. Contains `yolo_web_v3/yolo_web/models/best.pt` and `yolo_web_v3/yolo_web/data/history.db`. |
| Verification Status | ZIP SHA-256 independently verified on 2026-09-21 against the supplied value. Internal paths listed without extraction. Database contents were not read or copied. |
| Notes | The archive is retained outside the project repository and is explicitly ignored by project `.gitignore` patterns. Machine-specific locations must be supplied through local configuration or environment variables and must not be committed. |

## REF-002: Teacher PPE YOLO11n Checkpoint

| Field | Value |
| --- | --- |
| Asset ID | REF-002 |
| Asset Name | Teacher PPE YOLO11n Checkpoint |
| Provider | Teacher / course-provided |
| Original Filename | `models/best.pt` (inside REF-001 at `yolo_web_v3/yolo_web/models/best.pt`) |
| SHA-256 | `33eff6bf8aa250a19e13c8031de28787708263f3ee881a4519c9925c10d704c7` |
| Asset Type | External YOLO11n model checkpoint |
| License / Permission Status | TO VERIFY; no permission for public redistribution established |
| Repository Inclusion | NO |
| Purpose | BASELINE / REFERENCE for future controlled comparison and smoke testing |
| Allowed Usage | Phase 3 外部 baseline 对照；Phase 4 推理 smoke test；与自主训练 YOLO11 模型做结果比较 |
| Forbidden Usage | 替代 M-004 自主训练；声称老师 checkpoint 是本项目训练成果；在许可证/授权未明确前上传公开仓库 |
| Known Metadata | Model: YOLO11n. Classes: `0 head`, `1 ordinary_clothes`, `2 person`, `3 reflective_vest`, `4 safety_helmet`. Training config: base `yolo11n.pt`, epochs 300, batch 16, imgsz 640, optimizer AdamW, seed 0. Historical metrics: Precision 0.95716, Recall 0.85694, mAP50 0.94201, mAP50-95 0.71859. Checkpoint entry size: 5,505,050 bytes. |
| Verification Status | Checkpoint entry SHA-256 independently verified on 2026-09-21 by reading the ZIP entry stream without extraction. Training metadata is supplied/historical and has not been independently re-evaluated. |
| Notes | The metrics are checkpoint-stored historical training metadata. They are not project-measured results, not a reproduction by this project, and not current model validation results because the project test set has not been used. |

## Class Semantics

Teacher checkpoint classes:

```text
0 head
1 ordinary_clothes
2 person
3 reflective_vest
4 safety_helmet
```

Project locked classes:

```text
0 person
1 hardhat
2 no_hardhat
3 vest
4 no_vest
```

POTENTIAL SEMANTIC MAPPING — UNVERIFIED:

- `head` must not currently be written as `no_hardhat`.
- `ordinary_clothes` must not currently be written as `no_vest`.
- No direct class map is approved because the teacher training data definition
  and annotation policy are not available.
- Any future mapping requires evidence, a dedicated mapping test, and an ADR.

## Baseline Naming

Future evaluation and reports must preserve these distinct labels:

- `Teacher Baseline`: REF-002, external historical checkpoint metadata.
- `Project-trained Model`: the model produced by the project's own
  reproducible M-004 workflow.

## Charter Integrity

The normalized locked-body SHA-256 for
`docs/00_PROJECT_CHARTER.md`, excluding only routine status columns, is:

```text
9e48d2d5b3960b82cfbe5a93ae67c0ac035702bfd1a022865763fc19fe6d464c
```

This intake does not modify the locked final goal, MUST definitions, Extension
definitions, or explicit non-V1 scope.

## Security Boundary

- `yolo_web_v3.zip`: no repository inclusion.
- `best.pt`: no repository inclusion.
- `history.db`: no repository inclusion and no content inspection.
- API keys, `.env` files, credentials, and tokens: no copying or reuse.
- If a real credential is discovered in the reference package, treat it as
  exposed and do not use it.
