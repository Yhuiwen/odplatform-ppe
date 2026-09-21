import time

from utils.performance_utils import elapsed_seconds, timed, timer


def test_timer_context_manager_records_elapsed_time() -> None:
    with timer("test-block") as result:
        time.sleep(0.001)
    assert result["elapsed_seconds"] > 0


def test_timing_decorator_preserves_result_and_metadata() -> None:
    @timed
    def add(left: int, right: int) -> int:
        return left + right

    assert add(2, 3) == 5
    assert add.__name__ == "add"
    assert elapsed_seconds(time.perf_counter()) >= 0
