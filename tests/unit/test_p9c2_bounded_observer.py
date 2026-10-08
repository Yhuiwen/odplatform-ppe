from scripts.run_p9b_full_chain import BoundedRecorder


def test_observer_containers_remain_bounded_under_many_records(tmp_path):
    recorder = BoundedRecorder(tmp_path, limit=100)
    try:
        for frame in range(20_000):
            recorder.stage_samples.append({"frame_id": frame, "stage": "infer_frame", "ms": 1.0})
            recorder.frame_summaries.append({"frame_id": frame})
            recorder.timeline.append({"name": "frame", "frame_id": frame})
            recorder.associations.append({"frame_id": frame})
            recorder.association_candidates.append({"frame_id": frame})
            recorder.track_ids[frame] = [frame]
            recorder.track_details[frame] = [{"track_id": frame}]
            recorder.first_seen[(frame, "NO_HELMET")] = frame
            recorder.confirmed[(frame, "NO_HELMET")] = frame
            recorder.events[f"E{frame}"] = {"event_id": f"E{frame}"}
        assert all(len(getattr(recorder, name)) == 100 for name in (
            "stage_samples", "frame_summaries", "timeline", "associations",
            "association_candidates", "track_ids", "track_details",
            "first_seen", "confirmed", "events",
        ))
        assert recorder.stage_samples.count == 20_000
        assert recorder.stage_samples[0]["frame_id"] == 19_900
    finally:
        recorder.close()
    assert sum(1 for _ in (tmp_path / "metrics/stages.jsonl").open(encoding="utf-8")) == 20_000
