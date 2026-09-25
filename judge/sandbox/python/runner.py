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


IS_WINDOWS = os.name == "nt"
SIGKILL = getattr(signal, "SIGKILL", None)  # Windows pe SIGKILL exist nahi karta


def kill(proc):
    """Time limit cross -> process ko turant band karo."""
    try:
        if IS_WINDOWS:
            proc.kill()
        else:
            os.killpg(proc.pid, SIGKILL)  # poora group, taaki child processes bhi marein
    except (ProcessLookupError, OSError):
        pass


def read_limited(path, limit):
    with open(path, "rb") as f:
        data = f.read(limit + 1)
    return data


def run_one(code_path, inp, time_limit_s):
    in_path = os.path.join(WORKDIR, "input.txt")
    out_path = os.path.join(WORKDIR, "output.txt")
    err_path = os.path.join(WORKDIR, "stderr.txt")
    with open(in_path, "w", encoding="utf-8") as f:
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
            # Linux/Mac: apna process group, taaki poora group kill ho sake. Windows pe yeh nahi hota.
            start_new_session=not IS_WINDOWS,
        )
        try:
            rc = proc.wait(timeout=time_limit_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill(proc)
            rc = proc.wait()
    elapsed_ms = int((time.monotonic() - start) * 1000)

    stderr = read_limited(err_path, MAX_STDERR_BYTES).decode("utf-8", "replace")[-MAX_STDERR_BYTES:]
    if timed_out:
        return {"status": "TLE", "time_ms": elapsed_ms, "stderr": ""}
    if (SIGKILL is not None and rc == -SIGKILL) or "MemoryError" in stderr:
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
    with open(code_path, "w", encoding="utf-8") as f:
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
