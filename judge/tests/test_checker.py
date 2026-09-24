"""Checker ke unit tests. Docker ki zaroorat nahi, sandbox ko fake function se replace karte hain."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from checker import judge, normalize, outputs_match  # noqa: E402

TESTS = [
    {"input": "1 2\n", "expected": "3\n", "is_sample": True},
    {"input": "5 5\n", "expected": "10\n", "is_sample": False},
]


def make_job():
    return {"submission_id": 1, "code": "x", "language": "python",
            "time_limit_ms": 1000, "memory_limit_mb": 128, "tests": TESTS}


def fake_run(results):
    def run(**_):
        return {"results": results}
    return run


def test_normalize_ignores_trailing_whitespace():
    assert normalize("3  \n\n") == "3"
    assert outputs_match("a b \nc\n\n", "a b\nc")
    assert not outputs_match("3", "4")


def test_all_pass_is_ac():
    res = judge(make_job(), fake_run([
        {"status": "OK", "output": "3\n", "time_ms": 5},
        {"status": "OK", "output": "10", "time_ms": 7},
    ]))
    assert res["verdict"] == "AC"
    assert res["passed"] == 2 and res["runtime_ms"] == 7


def test_wrong_answer_on_sample_shows_details():
    res = judge(make_job(), fake_run([
        {"status": "OK", "output": "4\n", "time_ms": 5},
        {"status": "OK", "output": "10", "time_ms": 7},
    ]))
    assert res["verdict"] == "WA"
    assert res["passed"] == 1
    assert res["details"]["got"] == "4\n"


def test_hidden_test_failure_does_not_leak_input():
    res = judge(make_job(), fake_run([
        {"status": "OK", "output": "3", "time_ms": 5},
        {"status": "RE", "stderr": "boom", "time_ms": 7},
    ]))
    assert res["verdict"] == "RE"
    assert "details" not in res
    assert "hidden" in res["message"]


def test_tle_marks_remaining_tests_skipped():
    res = judge(make_job(), fake_run([{"status": "TLE", "time_ms": 1000}]))
    assert res["verdict"] == "TLE"
    assert [t["verdict"] for t in res["tests"]] == ["TLE", "SKIPPED"]


def test_crashed_sandbox_is_runtime_error():
    res = judge(make_job(), lambda **_: {"results": [], "crashed": True})
    assert res["verdict"] == "RE"
    assert res["passed"] == 0
