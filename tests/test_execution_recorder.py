"""Unit tests for ExecutionRecorder."""

from flock.functions.models import InvocationResult
from flock.functions.recorder import ExecutionRecorder


def test_recorder_history_indexing() -> None:
    recorder = ExecutionRecorder()
    res = InvocationResult(invocation_id="i1", success=True, output="output-data")

    recorder.record_result(res)
    assert recorder.get_result("i1") == res
    assert recorder.get_result("missing") is None
