"""Read-only local V1 deployment readiness check (no network or detection)."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]


def main():
    required=['docs/V1_DEPLOYMENT_GUIDE.md','docs/V1_DEMO_AND_DEFENSE.md',
              'docs/reports/phase-09/V1_COMPLETION_REPORT.md',
              'docs/reports/phase-09/V1_REAL_REPORT_VALIDATION.json',
              'docs/reports/phase-09/V1_SPLIT_R2_QUALITY.md',
              'docs/reports/phase-09/V1_SPLIT_R2_EVALUATION.json']
    missing=[p for p in required if not (ROOT/p).is_file()]
    if missing:
        print('Missing delivery evidence: '+', '.join(missing)); return 1
    result=subprocess.run([sys.executable,'scripts/preflight.py'],cwd=ROOT)
    if result.returncode: return result.returncode
    private=ROOT/'configs/llm.local.json'
    if private.exists():
        tracked=subprocess.check_output(['git','ls-files','--','configs/llm.local.json'],cwd=ROOT)
        if tracked.strip(): print('Private configuration is tracked'); return 1
        if subprocess.run(['git','check-ignore','-q','configs/llm.local.json'],cwd=ROOT).returncode:
            print('Private configuration is not ignored'); return 1
    print('V1 LOCAL DELIVERY CHECK: PASS (RTSP/long stability excluded)')
    return 0


if __name__=='__main__': raise SystemExit(main())
