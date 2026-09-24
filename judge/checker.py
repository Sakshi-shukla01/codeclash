"""
Checker: sandbox ke output ko expected output se compare karke verdict decide karta hai.

Verdicts:
  AC  = Accepted              WA  = Wrong Answer
  TLE = Time Limit Exceeded   RE  = Runtime Error
  MLE = Memory Limit Exceeded OLE = Output Limit Exceeded
  IE  = Internal Error (humari galti, user ki nahi)
"""
from typing import Callable

SHOW_CHARS = 300  # sample test pe user ko kitna input/output dikhana hai


def normalize(text: str) -> str:
    """Trailing spaces aur extra blank lines ignore karo (competitive programming standard)."""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)


def outputs_match(got: str, expected: str) -> bool:
    return normalize(got) == normalize(expected)


def _clip(s: str) -> str:
    return s if len(s) <= SHOW_CHARS else s[:SHOW_CHARS] + "..."


def judge(job: dict, run: Callable) -> dict:
    """
    job = {submission_id, code, language, time_limit_ms, memory_limit_mb,
           tests: [{input, expected, is_sample}]}
    run = sandbox function (test mein fake function pass kar sakte hain)
    """
    tests = job["tests"]
    total = len(tests)
    base = {"submission_id": job["submission_id"], "total": total}

    if job.get("language", "python") != "python":
        return {**base, "verdict": "IE", "passed": 0, "runtime_ms": 0,
                "tests": [], "message": "Only Python is supported right now."}

    sandbox_out = run(
        code=job["code"],
        inputs=[t["input"] for t in tests],
        time_limit_ms=job["time_limit_ms"],
        memory_limit_mb=job["memory_limit_mb"],
    )
    results = sandbox_out.get("results", [])

    per_test, passed, first_fail, max_time = [], 0, None, 0
    for i, test in enumerate(tests):
        if i >= len(results):
            # sandbox crash hua ya TLE ke baad tests skip hue
            verdict = "RE" if sandbox_out.get("crashed") and first_fail is None else "SKIPPED"
            per_test.append({"verdict": verdict, "time_ms": 0})
            if first_fail is None:
                first_fail = (i, verdict, {"stderr": "Sandbox process crashed"})
            continue

        r = results[i]
        max_time = max(max_time, r.get("time_ms", 0))
        if r["status"] == "OK":
            verdict = "AC" if outputs_match(r.get("output", ""), test["expected"]) else "WA"
        else:
            verdict = r["status"]  # TLE / RE / MLE / OLE
        per_test.append({"verdict": verdict, "time_ms": r.get("time_ms", 0)})
        if verdict == "AC":
            passed += 1
        elif first_fail is None:
            first_fail = (i, verdict, r)

    result = {**base, "passed": passed, "runtime_ms": max_time, "tests": per_test}
    if first_fail is None:
        result.update(verdict="AC", message="All test cases passed!")
        return result

    idx, verdict, raw = first_fail
    result["verdict"] = verdict
    test = tests[idx]
    if test.get("is_sample"):
        # Sample test pe poori details dikhao, taaki user debug kar sake
        result["message"] = f"{verdict} on sample test #{idx + 1}"
        result["details"] = {
            "input": _clip(test["input"]),
            "expected": _clip(test["expected"]),
            "got": _clip(raw.get("output", "")) if verdict == "WA" else None,
            "stderr": _clip(raw.get("stderr", "")) or None,
        }
    else:
        # Hidden test ka input/output leak nahi karna (warna log answers "print" karke cheat karenge)
        result["message"] = f"{verdict} on hidden test #{idx + 1}"
    return result
