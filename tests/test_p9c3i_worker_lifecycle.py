"""Fast deterministic controls for the diagnostic thread lifecycle harness."""

from pathlib import Path
from types import SimpleNamespace
from threading import get_ident

import pytest

from diagnostics.p9c3i_workers import PersistentCycleWorker, PersistentInferenceAdapter, run_in_fresh_worker
from scripts.run_p9c3i_worker_lifecycle import check_frame_semantics, infer_cycle, model_identity


class _FakeInference:
    def __init__(self):
        self.detector = SimpleNamespace(_model=object())
        self.calls = 0

    def infer_frame(self, frame, *, source):
        self.calls += 1
        return [SimpleNamespace(frame_id=frame.frame_id)]


def test_direct_driver_reuses_service_and_model():
    service = _FakeInference()
    frames = [SimpleNamespace(frame_id=i) for i in range(3)]
    before = model_identity(service)
    assert infer_cycle(service, frames, "source") == {"frames": 3, "detections": 3}
    assert infer_cycle(service, frames, "source") == {"frames": 3, "detections": 3}
    assert service.calls == 6
    assert model_identity(service) == before


def test_persistent_worker_keeps_same_thread_and_joins():
    main = get_ident()
    worker = PersistentCycleWorker(lambda *_: get_ident())
    try:
        first = worker.run_cycle((), "source")
        second = worker.run_cycle((), "source")
        assert first == second != main
        assert worker.created == 1
    finally:
        worker.close()
    assert worker.joined == 1


def test_fresh_worker_joins_each_cycle():
    main = get_ident()
    for _ in range(3):
        assert run_in_fresh_worker(lambda *_: get_ident(), (), "source") != main


def test_worker_exceptions_return_without_hanging():
    worker = PersistentCycleWorker(lambda *_: (_ for _ in ()).throw(ValueError("fail")))
    try:
        with pytest.raises(ValueError, match="fail"):
            worker.run_cycle((), "source")
    finally:
        worker.close()


def test_semantic_projection_rejects_count_mismatch():
    fixture = {"frames": [{"detections": [{"class_id": 0}]}]}
    with pytest.raises(AssertionError, match="count mismatch"):
        check_frame_semantics(0, (), fixture)


def test_persistent_inference_adapter_is_bounded_and_joins():
    service = _FakeInference()
    checked = []
    adapter = PersistentInferenceAdapter(service, lambda frame_id, found: checked.append((frame_id, len(found))))
    try:
        assert adapter._requests.maxsize == 1
        first = adapter.infer_frame(SimpleNamespace(frame_id=0), source="source")
        second = adapter.infer_frame(SimpleNamespace(frame_id=1), source="source")
        assert [first[0].frame_id, second[0].frame_id] == [0, 1]
        assert checked == [(0, 1), (1, 1)]
        assert service.calls == 2
    finally:
        adapter.shutdown()
    assert adapter.created == adapter.joined == 1
    with pytest.raises(RuntimeError, match="shut down"):
        adapter.infer_frame(SimpleNamespace(frame_id=2), source="source")


def test_no_heavy_observer_imports():
    root = Path(__file__).resolve().parents[1]
    runner = (root / "scripts/run_p9c3i_worker_lifecycle.py").read_text(encoding="utf-8")
    for forbidden in ("tracemalloc", "gc.get_objects", "BoundedRecorder", "ObservedInference"):
        assert forbidden not in runner
