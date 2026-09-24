"""
Sandbox runner: yeh file Docker container ke ANDAR chalti hai (user 'nobody' ke roop mein).

stdin se JSON aata hai:  {"code": "...", "inputs": ["...", "..."], "time_limit_ms": 2000}
stdout pe JSON jaata hai: {"results": [{"status": "OK", "output": "...", "time_ms": 12}, ...]}

Note: runner ko expected outputs NAHI diye jaate. Compare karna judge worker ka kaam hai
(jo sandbox ke bahar trusted jagah pe chalta hai). Isliye user code chahe runner ko
tod bhi de, sahi answer "fake" nahi kar sakta.
"""
import json
import os
import signal
import subprocess
import sys
import time

WORKDIR = os.environ.get("SANDBOX_WORKDIR", "/tmp")
MAX_OUTPUT_BYTES = 4 * 1024 * 1024  # 4MB se zyada output = Output Limit Exceeded
MAX_STDERR_BYTES = 2000


def read_limited(path, limit):
    with open(path, "rb") as f:
        data = f.read(limit + 1)
    return data


def run_one(code_path, inp, time_limit_s):
    in_path = os.path.join(WORKDIR, "input.txt")
    out_path = os.path.join(WORKDIR, "output.txt")
    err_path = os.path.join(WORKDIR, "stderr.txt")
    with open(in_path, "w") as f:
        f.write(inp)

    start = time.monotonic()
    timed_out = False
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout, open(err_path, "wb") as ferr:
        proc = subprocess.Popen(
            [sys.executable, "-B", code_path],
            stdin=fin,
            stdout=fout,
            stderr=ferr,
            cwd=WORKDIR,
            start_new_session=True,  # apna process group, taaki poora group kill ho sake
        )
        try:
            rc = proc.wait(timeout=time_limit_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            rc = proc.wait()
    elapsed_ms = int((time.monotonic() - start) * 1000)

    stderr = read_limited(err_path, MAX_STDERR_BYTES).decode("utf-8", "replace")[-MAX_STDERR_BYTES:]
    if timed_out:
        return {"status": "TLE", "time_ms": elapsed_ms, "stderr": ""}
    if rc == -signal.SIGKILL or "MemoryError" in stderr:
        # cgroup memory limit cross hone pe kernel process ko SIGKILL karta hai
        return {"status": "MLE", "time_ms": elapsed_ms, "stderr": stderr}
    if rc != 0:
        return {"status": "RE", "time_ms": elapsed_ms, "stderr": stderr, "exit_code": rc}

    out = read_limited(out_path, MAX_OUTPUT_BYTES)
    if len(out) > MAX_OUTPUT_BYTES:
        return {"status": "OLE", "time_ms": elapsed_ms, "stderr": ""}
    return {"status": "OK", "time_ms": elapsed_ms, "output": out.decode("utf-8", "replace"), "stderr": stderr}


def main():
    job = json.loads(sys.stdin.read())
    time_limit_s = job["time_limit_ms"] / 1000.0
    code_path = os.path.join(WORKDIR, "solution.py")
    with open(code_path, "w") as f:
        f.write(job["code"])

    results = []
    for inp in job["inputs"]:
        res = run_one(code_path, inp, time_limit_s)
        results.append(res)
        if res["status"] == "TLE":
            break  # TLE ke baad baaki tests chalana time ki barbaadi hai

    sys.stdout.write(json.dumps({"results": results}))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
