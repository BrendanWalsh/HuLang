"""Exercise the installer without downloading or installing dependencies."""

import os
import subprocess
from pathlib import Path

import pytest

INSTALLER = Path(__file__).resolve().parents[1] / "install.sh"


@pytest.fixture
def installer_env(tmp_path):
    tools = tmp_path / "tools"
    tools.mkdir()
    prefix = tmp_path / "prefix"
    scripts = {
        "python3": """#!/bin/bash
set -eu
if [ "$1" = "-c" ]; then exit 0; fi
mkdir -p "$3/bin"
cp "$FAKE_TOOLS/venv-python" "$3/bin/python"
cp "$FAKE_TOOLS/installed-nlc" "$3/bin/nlc"
""",
        "venv-python": """#!/bin/bash
printf '%s\\n' "$*" >> "$INSTALL_LOG"
exit "${PIP_EXIT:-0}"
""",
        "installed-nlc": "#!/bin/bash\nprintf 'nlc (hulang) installed\\n'\n",
        "gcc": "#!/bin/bash\nexit 0\n",
        "copilot": "#!/bin/bash\nexit 0\n",
        "curl": "#!/bin/bash\nexit 99\n",
    }
    for name, content in scripts.items():
        tool = tools / name
        tool.write_text(content)
        tool.chmod(0o755)
    return {
        **os.environ,
        "PATH": f"{tools}:{os.environ['PATH']}",
        "HULANG_PREFIX": str(prefix),
        "HULANG_SOURCE": "/local/source",
        "FAKE_TOOLS": str(tools),
        "INSTALL_LOG": str(tmp_path / "install.log"),
    }


def test_installs_and_can_rerun(installer_env):
    for _ in range(2):
        result = subprocess.run(["bash", str(INSTALLER)], env=installer_env, capture_output=True)
        assert result.returncode == 0, result.stderr.decode()
        assert b"nlc (hulang) installed" in result.stdout
    prefix = Path(installer_env["HULANG_PREFIX"])
    assert (prefix / "bin/nlc").resolve() == prefix / "share/hulang/venv/bin/nlc"
    assert Path(installer_env["INSTALL_LOG"]).read_text().splitlines() == [
        "-m pip install --quiet --upgrade /local/source",
        "-m pip install --quiet --upgrade /local/source",
    ]


def test_refuses_to_replace_unrelated_command(installer_env):
    command = Path(installer_env["HULANG_PREFIX"]) / "bin/nlc"
    command.parent.mkdir(parents=True)
    command.write_text("keep me")
    result = subprocess.run(["bash", str(INSTALLER)], env=installer_env, capture_output=True)
    assert result.returncode == 1
    assert b"not managed by this installer" in result.stderr
    assert command.read_text() == "keep me"


def test_install_failure_is_reported(installer_env):
    result = subprocess.run(
        ["bash", str(INSTALLER)],
        env={**installer_env, "PIP_EXIT": "42"},
        capture_output=True,
    )
    assert result.returncode == 42
    assert b"Installed." not in result.stdout
    assert not (Path(installer_env["HULANG_PREFIX"]) / "bin/nlc").exists()
