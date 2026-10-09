"""Run the existing monitoring pipeline through the local API in isolated storage."""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep

from fastapi.testclient import TestClient
from api.main import app


VIDEO = Path('artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4').resolve()


def main() -> None:
    if not VIDEO.is_file():
        print('NOT_EXECUTED: verified local MP4 is absent')
        return
    with TemporaryDirectory(prefix='odplatform-frontend-mp4-') as root:
        os.environ['ODPLATFORM_P9B_VALIDATION_ROOT'] = root
        with TestClient(app) as client:
            response = client.post('/api/v1/monitor/start', json={'source_type': 'mp4', 'location': str(VIDEO)})
            if response.status_code != 200:
                raise RuntimeError(f'start failed: HTTP {response.status_code} {response.text}')
            deadline = monotonic() + 180
            while monotonic() < deadline:
                status = client.get('/api/v1/monitor/status').json()
                if status['state'] in {'completed', 'stopped', 'failed'}:
                    print({key: status.get(key) for key in ('state', 'frames_processed', 'detections', 'events_generated', 'alerts_delivered', 'has_preview', 'error_code')})
                    if status['state'] != 'completed' or status['frames_processed'] == 0 or not status['has_preview']:
                        raise RuntimeError('monitoring did not complete with processed preview')
                    return
                sleep(1)
            client.post('/api/v1/monitor/stop')
            raise RuntimeError('monitoring completion timed out')


if __name__ == '__main__':
    main()
