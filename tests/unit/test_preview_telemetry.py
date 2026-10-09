from api.preview_telemetry import PreviewTelemetry


def test_preview_timing_uses_published_frames_only():
    now = [0.0]
    published = []
    telemetry = PreviewTelemetry(lambda frame_id, image: published.append(frame_id), clock=lambda: now[0])
    assert telemetry.status(running=True) == {'preview_fps': None, 'preview_age_ms': None}
    for frame_id, timestamp in [(1, 0.0), (2, 0.05), (3, 0.1)]:
        now[0] = timestamp
        telemetry.publish(frame_id, object())
    now[0] = 0.12
    assert telemetry.status(running=True) == {'preview_fps': 20.0, 'preview_age_ms': 20}
    assert published == [1, 2, 3]
    assert telemetry.status(running=False) == {'preview_fps': None, 'preview_age_ms': None}
    now[0] = 4.0
    assert telemetry.status(running=True) == {'preview_fps': None, 'preview_age_ms': None}


def test_failed_preview_publish_is_not_counted():
    def fail(frame_id, image):
        raise ValueError('encode failed')

    telemetry = PreviewTelemetry(fail, clock=lambda: 1.0)
    try:
        telemetry.publish(1, object())
    except ValueError:
        pass
    assert telemetry.status(running=True) == {'preview_fps': None, 'preview_age_ms': None}
