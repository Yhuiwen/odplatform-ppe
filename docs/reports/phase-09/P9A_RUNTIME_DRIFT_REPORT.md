# P9-A Runtime Drift and FINAL-DEMO-RUNTIME-001 Freeze

Date: 2026-09-25. Status: FROZEN / VALIDATED after P9-A.1.

`INF-RUNTIME-001` remains immutable. The Phase 7 runtime is an observed,
successful Windows 11 AMD64 CPU environment, not an interchangeable lock.
The final demo runtime was created in `.venv-final-demo` with Python 3.12.1,
validated, then locked from its actual `pip freeze`. No model download occurred.

| Dependency | INF-RUNTIME-001 / EVAL lock | Phase 7 observed | Root requirements | FINAL-DEMO candidate |
| --- | --- | --- | --- | --- |
| Python | 3.10.4 | 3.12.1 | >=3.10 in pyproject | 3.12.1, validated |
| torch | 2.5.1+cpu (lock 2.5.1) | 2.5.1+cpu | transitive only | 2.5.1+cpu |
| torchvision | 0.20.1 | 0.20.1+cpu | transitive only | 0.20.1+cpu |
| ultralytics | 8.4.157 | 8.4.157 | >=8.3,<9 | 8.4.157 |
| opencv-python | 5.0.0.93 | 5.0.0 | ==5.0.0.93 **RESOLVED** | 5.0.0.93 |
| numpy | 2.2.6 | 2.2.6 (P7-5) | transitive only | 2.2.6 |
| Pillow | 12.3.0 | not individually recorded | >=10,<13 | 12.3.0 |
| Streamlit | absent | 1.64.0 | >=1.39,<2 | 1.64.0 |
| pytest | 8.3.4 | not individually recorded | >=8,<9 | 8.3.4 |
| pyttsx3 | absent | 2.99, native SAPI PASS | >=2.90,<3 | 2.99 |
| plotly | absent | not individually recorded | >=5.24,<7 | 6.9.0, installed |
| PyYAML | 6.0.3 | not individually recorded | >=6,<7 | 6.0.3 |

`pyproject.toml` intentionally declares `dependencies = []` and explicitly
documents that `pip install .` alone is not the full application install.
`locks/FINAL-DEMO-RUNTIME-001/requirements.txt` is the authoritative runtime
installation entry. Root requirements now pin OpenCV 5.0.0.93, and
`pip install -r requirements.txt`, `pip check`, real image and MP4 runs passed.

Runtime identity: Windows 11 AMD64, CPU only, no CUDA, no automatic weight
download. Checkpoint: `models/checkpoints/EXP-001/best.pt`, SHA256
`1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`.
Inference configuration: `configs/inference.yaml`, SHA256
`0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c`.
The 78-package lock SHA256 is
`3a22bc1a70801a318aff5e616472af3f3c9ecfb63c6c4e9bf9af370e359984`.
The freeze covers runtime capability only; P9-B full-chain acceptance remains
pending. See `P9A_FINAL_DEMO_RUNTIME_FREEZE_REPORT.md` for commands/results.
