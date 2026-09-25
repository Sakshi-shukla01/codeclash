"""
Sandbox integration tests: asli code chalake dekhte hain ki "bura" code system ko tod na paaye.

Chalane ka tarika (Docker + sandbox image chahiye):
    docker compose build sandbox-python
    cd judge && JUDGE_MODE=docker pytest tests/test_sandbox_attacks.py -v

Bina Docker ke (JUDGE_MODE=local) sirf woh tests chalte hain jo isolation pe depend nahi karte.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sandbox import SANDBOX_IMAGE, run_in_sandbox  # noqa: E402

MODE = os.environ.get("JUDGE_MODE", "docker")


def docker_ready():
    if not shutil.which("docker"):
        return False
    r = subprocess.run(["docker", "image", "inspect", SANDBOX_IMAGE], capture_output=True)
    return r.returncode == 0


needs_docker = pytest.mark.skipif(
    MODE != "docker" or not docker_ready(), reason="needs Docker + sandbox image"
)
if MODE == "docker" and not docker_ready():
    pytestmark = pytest.mark.skip(reason="Docker/sandbox image not available")


def run(code, inputs=("",), tl=1000):
    return run_in_sandbox(code, list(inputs), time_limit_ms=tl, memory_limit_mb=128)["results"]


def test_normal_code_runs():
    res = run("a,b=map(int,input().split());print(a+b)", ["2 3\n"])
    assert res[0]["status"] == "OK" and res[0]["output"].strip() == "5"


def test_infinite_loop_is_tle():
    res = run("while True: pass", tl=500)
    assert res[0]["status"] == "TLE"


def test_exception_is_runtime_error():
    res = run("print(1/0)")
    assert res[0]["status"] == "RE"
    assert "ZeroDivisionError" in res[0]["stderr"]


@needs_docker
def test_memory_bomb_is_mle():
    res = run("x = bytearray(1024*1024*1024)")
    assert res[0]["status"] == "MLE"


@needs_docker
def test_no_network():
    code = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('8.8.8.8', 53), timeout=2); print('CONNECTED')\n"
        "except Exception as e:\n"
        "    print('BLOCKED')\n"
    )
    assert run(code)[0]["output"].strip() == "BLOCKED"


@needs_docker
def test_filesystem_is_read_only():
    code = (
        "try:\n"
        "    open('/etc/hacked', 'w').write('x'); print('WROTE')\n"
        "except Exception:\n"
        "    print('DENIED')\n"
    )
    assert run(code)[0]["output"].strip() == "DENIED"


@needs_docker
def test_runs_as_nobody():
    assert run("import os; print(os.getuid())")[0]["output"].strip() == "65534"


@needs_docker
def test_fork_bomb_is_contained():
    code = (
        "import os\n"
        "n = 0\n"
        "try:\n"
        "    while True:\n"
        "        if os.fork() == 0:\n"
        "            import time; time.sleep(5); os._exit(0)\n"
        "        n += 1\n"
        "except OSError:\n"
        "    print('LIMITED', n)\n"
    )
    res = run(code, tl=2000)
    assert res[0]["status"] in ("OK", "TLE", "RE")
    if res[0]["status"] == "OK":
        assert res[0]["output"].startswith("LIMITED")


def test_unicode_code_and_output():
    # Windows pe default encoding UTF-8 nahi hoti, yeh test ensure karta hai ki Hindi/emoji wala code chale
    res = run("# नमस्ते ⚔️\nprint('जीत 🏆')")
    assert res[0]["status"] == "OK" and res[0]["output"].strip() == "जीत 🏆"
