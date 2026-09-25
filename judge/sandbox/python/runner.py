"""
Sandbox runner: yeh file Docker container ke ANDAR chalti hai (user 'nobody' ke roop mein).
Local mode mein yahi file seedha laptop pe chalti hai.

stdin se JSON aata hai:
    {"code": "...", "language": "cpp", "inputs": ["...", "..."], "time_limit_ms": 2000}
stdout pe JSON jaata hai (teen mein se ek):
    {"results": [{"status": "OK", "output": "...", "time_ms": 12}, ...]}
    {"compile_error": "error message"}          -> user ke code mein compile error
    {"judge_error": "g++ not found ..."}        -> judge machine pe compiler install nahi

Supported languages: python, cpp, c, java, javascript  (LANGUAGES dict dekho)

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
COMPILE_TIMEOUT_S = 30

IS_WINDOWS = os.name == "nt"
SIGKILL = getattr(signal, "SIGKILL", None)  # Windows pe SIGKILL exist nahi karta
EXE = os.path.join(WORKDIR, "solution.exe" if IS_WINDOWS else "solution")

# Har language: source file ka naam, compile command (ya None), run command, aur time multiplier.
# Java/JavaScript ka startup slow hota hai, isliye unhe thoda extra time milta hai (LeetCode bhi aisa karta hai).
LANGUAGES = {
    "python": {
        "file": "solution.py",
        "compile": None,
        "run": lambda src: [sys.executable, "-B", src],
        "time_factor": 1.0,
    },
    "cpp": {
        "file": "solution.cpp",
        "compile": lambda src: ["g++", "-O2", "-std=c++17", "-o", EXE, src],
        "run": lambda src: [EXE],
        "time_factor": 1.0,
    },
    "c": {
        "file": "solution.c",
        "compile": lambda src: ["gcc", "-O2", "-std=c11", "-o", EXE, src, "-lm"],
        "run": lambda src: [EXE],
        "time_factor": 1.0,
    },
    "java": {
        "file": "Main.java",  # public class ka naam Main hona chahiye
        "compile": lambda src: ["javac", "-encoding", "UTF-8", "-d", WORKDIR, src],
        "run": lambda src: ["java", "-Xss64m", "-Xmx160m", "-XX:+UseSerialGC", "-XX:-UsePerfData",
                            "-cp", WORKDIR, "Main"],
        "time_factor": 2.0,
    },
    "javascript": {
        "file": "solution.js",
        "compile": None,
        "run": lambda src: ["node", "--stack-size=65500", src],
        "time_factor": 1.5,
    },
}

MEMORY_ERROR_MARKERS = ("MemoryError", "OutOfMemoryError", "std::bad_alloc", "heap out of memory")


def child_env():
    """User code ko ek saaf environment do (judge machine ki settings leak na hon)."""
    env = {k: v for k, v in os.environ.items() if k not in ("JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS")}
    env["PYTHONUTF8"] = "1"
    return env


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
        return f.read(limit + 1)


def compile_code(lang, src):
    """Return None agar sab theek, warna {"compile_error": ...} ya {"judge_error": ...}."""
    cmd = lang["compile"](src)
    try:
        proc = subprocess.run(cmd, cwd=WORKDIR, capture_output=True, timeout=COMPILE_TIMEOUT_S, env=child_env())
    except FileNotFoundError:
        return {"judge_error": f"Compiler '{cmd[0]}' is not installed on the judge machine."}
    except subprocess.TimeoutExpired:
        return {"compile_error": f"Compilation took longer than {COMPILE_TIMEOUT_S} seconds."}
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout).decode("utf-8", "replace")
        msg = msg.replace(WORKDIR + os.sep, "").replace(WORKDIR, "")  # temp folder ka path mat dikhao
        return {"compile_error": msg[:MAX_STDERR_BYTES] or "Compilation failed."}
    return None


def run_one(run_cmd, inp, time_limit_s):
    in_path = os.path.join(WORKDIR, "input.txt")
    out_path = os.path.join(WORKDIR, "output.txt")
    err_path = os.path.join(WORKDIR, "stderr.txt")
    with open(in_path, "w", encoding="utf-8") as f:
        f.write(inp)

    start = time.monotonic()
    timed_out = False
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout, open(err_path, "wb") as ferr:
        proc = subprocess.Popen(
            run_cmd,
            stdin=fin,
            stdout=fout,
            stderr=ferr,
            cwd=WORKDIR,
            env=child_env(),
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
    if (SIGKILL is not None and rc == -SIGKILL) or any(m in stderr for m in MEMORY_ERROR_MARKERS):
        # cgroup memory limit cross hone pe kernel process ko SIGKILL karta hai
        return {"status": "MLE", "time_ms": elapsed_ms, "stderr": stderr}
    if rc != 0:
        return {"status": "RE", "time_ms": elapsed_ms, "stderr": stderr, "exit_code": rc}

    out = read_limited(out_path, MAX_OUTPUT_BYTES)
    if len(out) > MAX_OUTPUT_BYTES:
        return {"status": "OLE", "time_ms": elapsed_ms, "stderr": ""}
    return {"status": "OK", "time_ms": elapsed_ms, "output": out.decode("utf-8", "replace"), "stderr": stderr}


def main():
    job = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    lang = LANGUAGES.get(job.get("language", "python"))
    if lang is None:
        sys.stdout.write(json.dumps({"judge_error": f"Unsupported language: {job.get('language')}"}))
        return

    src = os.path.join(WORKDIR, lang["file"])
    with open(src, "w", encoding="utf-8") as f:
        f.write(job["code"])

    if lang["compile"]:
        err = compile_code(lang, src)
        if err:
            sys.stdout.write(json.dumps(err))
            return

    time_limit_s = job["time_limit_ms"] / 1000.0 * lang["time_factor"]
    run_cmd = lang["run"](src)
    results = []
    for inp in job["inputs"]:
        try:
            res = run_one(run_cmd, inp, time_limit_s)
        except FileNotFoundError:
            sys.stdout.write(json.dumps({"judge_error": f"'{run_cmd[0]}' is not installed on the judge machine."}))
            return
        results.append(res)
        if res["status"] == "TLE":
            break  # TLE ke baad baaki tests chalana time ki barbaadi hai

    sys.stdout.write(json.dumps({"results": results}))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
