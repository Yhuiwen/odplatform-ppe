"""The preview transport exposes only the newest session-owned JPEG."""

from urllib.error import HTTPError
from urllib.request import urlopen

import numpy as np
import pytest

from web.monitoring_preview import PreviewChannel, PreviewHub


def test_preview_stream_serves_published_jpeg_and_rejects_other_tokens() -> None:
    hub = PreviewHub()
    try:
        channel = PreviewChannel()
        url = hub.register(channel)
        channel.publish(0, np.zeros((32, 48, 3), dtype=np.uint8))

        with urlopen(url, timeout=2) as response:
            assert response.headers.get_content_type() == "multipart/x-mixed-replace"
            assert response.readline() == b"--frame\r\n"
            assert response.readline() == b"Content-Type: image/jpeg\r\n"
            length = int(response.readline().split(b": ", 1)[1])
            assert response.readline() == b"\r\n"
            first = response.read(length)
            assert first.startswith(b"\xff\xd8")
            assert response.readline() == b"\r\n"

            channel.publish(1, np.full((32, 48, 3), 255, dtype=np.uint8))
            assert response.readline() == b"--frame\r\n"
            assert response.readline() == b"Content-Type: image/jpeg\r\n"
            next_length = int(response.readline().split(b": ", 1)[1])
            assert response.readline() == b"\r\n"
            second = response.read(next_length)
            assert second.startswith(b"\xff\xd8") and second != first

        with pytest.raises(HTTPError) as error:
            urlopen(url + "-invalid", timeout=2)
        assert error.value.code == 404
    finally:
        hub.close()
