"""
Sandbox: user ke code ko safely chalana.

Do modes hain (JUDGE_MODE env variable se):
  docker (default) -> har submission ek naye, band Docker container mein chalta hai. PRODUCTION ke liye.
  local            -> runner.py seedha is machine pe chalta hai, BINA isolation ke.
                      Sirf development/testing ke liye, jab Docker available na ho.
"""
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

log = logging.getLogger("judge.sandbox")

SANDBOX_IMAGE = os.environ.get("SANDBOX_IMAGE", "codeclash-sandbox-python:latest")
JUDGE_MODE = os.environ.get("JUDGE_MODE", "docker")
RUNNER_PATH = Path(__file__).parent / "sandbox" / "python" / "runner.py"


class SandboxError(Exception):
    """Sandbox khud fail ho gaya (user ki galti nahi, system ki)."""


def docker_command(container_name: str, memory_limit_mb: int) -> list[str]:
    return [
        "docker", "run",
        "--rm",                                  # kaam khatam -> container delete
        "-i",                                    # stdin se job JSON bhejenge
        "--name", container_name,
        "--network", "none",                     # internet band
        f"--memory={memory_limit_mb}m",          # RAM limit
        f"--memory-swap={memory_limit_mb}m",     # swap bhi band (warna limit bypass)
        "--cpus=1",                              # max 1 CPU core
        "--pids-limit=128",                      # fork bomb se bachav (Java/Node threads ke liye 128)
        "--read-only",                           # root filesystem read-only
        # sirf /tmp mein likh sakta hai (128MB). "exec" isliye ki C++/C ka compiled program yahin se chalta hai
        "--tmpfs", "/tmp:rw,exec,size=128m,mode=1777",
        "--user", "65534:65534",                 # nobody user, root nahi
        "--cap-drop=ALL",                        # saari Linux capabilities hatao
        "--security-opt", "no-new-privileges",   # sudo/setuid se power nahi badha sakta
        SANDBOX_IMAGE,
        "python", "/runner.py",
    ]


def run_in_sandbox(code: str, inputs: list[str], time_limit_ms: int, memory_limit_mb: int,
                   language: str = "python") -> dict:
    """
    Code ko saare inputs pe chalao. Return (runner.py ka output):
      {"results": [...]}  ya  {"compile_error": "..."}  ya  {"judge_error": "..."}
    """
    payload = json.dumps({"code": code, "language": language, "inputs": inputs, "time_limit_ms": time_limit_ms})
    # poore sandbox ka max time: compile (max 30s) + har test ka time limit (Java ko 2x) + startup
    overall_timeout = 30 + len(inputs) * (time_limit_ms / 1000 * 2 + 0.5) + 15

    workdir = None
    if JUDGE_MODE == "local":
        workdir = tempfile.mkdtemp(prefix="cc-sbx-")
        cmd = [sys.executable, str(RUNNER_PATH)]
        # PYTHONUTF8: Windows pe bhi UTF-8 use ho (warna Hindi/emoji wale code pe crash)
        env = {**os.environ, "SANDBOX_WORKDIR": workdir, "PYTHONUTF8": "1"}
        name = None
    else:
        name = f"cc-sbx-{uuid.uuid4().hex[:12]}"
        cmd = docker_command(name, memory_limit_mb)
        env = None

    try:
        proc = subprocess.run(
            cmd, input=payload, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=overall_timeout, env=env,
        )
    except subprocess.TimeoutExpired:
        if name:
            subprocess.run(["docker", "kill", name], capture_output=True)
        raise SandboxError("sandbox overall timeout")
    except FileNotFoundError as e:
        raise SandboxError(f"docker CLI not found: {e}")
    finally:
        if workdir:
            shutil.rmtree(workdir, ignore_errors=True)

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        # Runner hi crash ho gaya (jaise user ne runner ko kill kar diya, ya container OOM).
        log.warning("sandbox returned no JSON. rc=%s stderr=%s", proc.returncode, proc.stderr[-500:])
        if "Unable to find image" in proc.stderr or "No such image" in proc.stderr:
            raise SandboxError(f"sandbox image '{SANDBOX_IMAGE}' missing. Run: docker compose build")
        if "Cannot connect to the Docker daemon" in proc.stderr:
            raise SandboxError("docker daemon not reachable")
        return {"results": [], "crashed": True}
