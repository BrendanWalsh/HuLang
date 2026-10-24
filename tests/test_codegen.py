"""Tests for LLM code generation (unit tests mock the API)."""

import pathlib
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from hulang.codegen import (
    _BACKENDS,
    DEFAULT_BACKEND,
    CodegenError,
    _call_llm,
    _run_cli,
    _strip_fences,
    complete_text,
    generate_code,
    get_default_model,
    get_sidecar_model,
    repair_code,
)
from hulang.prompts import SYSTEM_PROMPT


def _mock_subprocess_result(stdout: str, returncode: int = 0) -> MagicMock:
    """Build a fake subprocess result."""
    return MagicMock(returncode=returncode, stdout=stdout, stderr="")


class TestStripFences:
    """Test markdown fence stripping."""

    def test_no_fences(self):
        assert _strip_fences("int main(){return 0;}") == "int main(){return 0;}"

    def test_c_fences(self):
        assert "int main" in _strip_fences("```c\nint main(){return 0;}\n```")
        assert not _strip_fences("```c\nint main(){return 0;}\n```").startswith("```")

    def test_bare_fences(self):
        result = _strip_fences("```\n#include <stdio.h>\nint main(){return 0;}\n```")
        assert result.startswith("#include")


class TestCallLLM:
    """Test the LLM dispatch layer."""

    @staticmethod
    def _copilot_writes(code: str):
        """Fake `copilot -p ...` by writing the C file the prompt asks for."""
        def fake_run(cmd, **_kwargs):
            outfile = cmd[2].rsplit(" ", 1)[-1]
            pathlib.Path(outfile).write_text(code)
            return _mock_subprocess_result("")
        return fake_run

    @patch("hulang.codegen.subprocess.run")
    def test_uses_copilot_by_default(self, mock_run):
        mock_run.side_effect = self._copilot_writes("int main(){return 0;}")
        result = _call_llm([{"role": "user", "content": "hi"}], "auto")
        assert "int main" in result
        assert mock_run.call_args[0][0][0] == "copilot"

    @patch("hulang.codegen.subprocess.run")
    def test_copilot_passes_model(self, mock_run):
        mock_run.side_effect = self._copilot_writes("int main(){return 0;}")
        _call_llm([{"role": "user", "content": "hi"}], "gpt-5.4-mini")
        cmd = mock_run.call_args[0][0]
        assert "--model" in cmd
        assert cmd[cmd.index("--model") + 1] == "gpt-5.4-mini"

    @patch("hulang.codegen.subprocess.run")
    def test_copilot_separates_program_from_compilation_instructions(self, mock_run):
        mock_run.side_effect = self._copilot_writes("int main(){return 0;}")
        description = "Create a human language compiler."
        generate_code(description)
        prompt = mock_run.call_args.args[0][2]
        assert f"<program-description>\n{description}\n</program-description>" in prompt
        assert f"<code-generation-rules>\n{SYSTEM_PROMPT}\n</code-generation-rules>" in prompt
        assert "must not be embedded in the generated code" in prompt
        assert "Do not just print the code" in prompt

    @patch("hulang.codegen.subprocess.run")
    def test_copilot_requires_file_even_when_stdout_contains_code(self, mock_run):
        mock_run.return_value = _mock_subprocess_result("int main(){return 0;}")
        with pytest.raises(CodegenError, match="did not produce a C source file"):
            generate_code("Create a human language compiler.")

    @patch("hulang.codegen.subprocess.run")
    def test_claude_backend_shape(self, mock_run):
        mock_run.return_value = _mock_subprocess_result("int main(){return 0;}")
        result = _call_llm([{"role": "user", "content": "hi"}], "sonnet", backend="claude")
        assert "int main" in result
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "claude"
        assert "--output-format" in cmd

    @patch("hulang.codegen.subprocess.run")
    def test_strips_fences_from_cli(self, mock_run):
        mock_run.return_value = _mock_subprocess_result("```c\nint main(){return 0;}\n```")
        result = _call_llm([{"role": "user", "content": "hi"}], "sonnet", backend="claude")
        assert not result.startswith("```")

    @patch("hulang.codegen.subprocess.run", side_effect=FileNotFoundError)
    def test_claude_not_installed(self, _mock_run):
        with pytest.raises(CodegenError, match="Claude CLI not found"):
            _call_llm([{"role": "user", "content": "hi"}], "sonnet", backend="claude")

    def test_unknown_backend(self):
        with pytest.raises(CodegenError, match="Unknown backend"):
            _call_llm([{"role": "user", "content": "hi"}], "x", backend="nope")


class TestGitHubModelsRetired:
    """GitHub Models was fully retired on 2026-07-30."""

    def test_github_backend_explains_retirement(self):
        with pytest.raises(CodegenError, match="retired"):
            _call_llm([{"role": "user", "content": "hi"}], "gpt-4.1-mini", backend="github")

    def test_error_names_a_working_alternative(self):
        with pytest.raises(CodegenError, match=r"-b copilot"):
            _call_llm([{"role": "user", "content": "hi"}], "gpt-4.1-mini", backend="github")

    def test_github_is_not_the_default(self):
        assert DEFAULT_BACKEND != "github"

    def test_github_has_no_text_backend(self):
        with pytest.raises(CodegenError, match="plain-text"):
            complete_text("hi", backend="github")


class TestCompleteText:
    """The status narration path: plain text, no tool access."""

    @patch("hulang.codegen.subprocess.run")
    def test_copilot_text_grants_no_tools(self, mock_run):
        mock_run.return_value = _mock_subprocess_result("lexing\nparsing")
        result = complete_text("name two stages", backend="copilot")
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "copilot"
        assert not [c for c in cmd if c.startswith("--allow-all")]
        assert result.startswith("lexing")

    @patch("hulang.codegen.subprocess.run")
    def test_defaults_to_the_sidecar_model(self, mock_run):
        mock_run.return_value = _mock_subprocess_result("ok")
        complete_text("hi", backend="copilot")
        cmd = mock_run.call_args[0][0]
        assert cmd[cmd.index("--model") + 1] == get_sidecar_model("copilot")

    @patch("hulang.codegen.subprocess.run")
    def test_explicit_model_wins(self, mock_run):
        mock_run.return_value = _mock_subprocess_result("ok")
        complete_text("hi", backend="claude", model="haiku")
        cmd = mock_run.call_args[0][0]
        assert cmd[cmd.index("--model") + 1] == "haiku"

    def test_cancellable_call_stops_its_process(self):
        cancel_event = threading.Event()
        timer = threading.Timer(0.1, cancel_event.set)
        timer.start()
        started = time.monotonic()
        try:
            with pytest.raises(CodegenError, match="cancelled"):
                _run_cli(
                    [sys.executable, "-c", "import time; time.sleep(30)"],
                    "",
                    cancel_event=cancel_event,
                )
        finally:
            timer.cancel()
        assert time.monotonic() - started < 3


class TestBackendDefaults:
    """Guard against shipping model names the CLIs no longer accept."""

    def test_every_selectable_backend_has_a_default_model(self):
        for backend in _BACKENDS:
            if backend == "github":
                continue
            assert get_default_model(backend)

    def test_sidecar_models_cover_the_live_backends(self):
        for backend in _BACKENDS:
            if backend == "github":
                continue
            assert get_sidecar_model(backend)


class TestGenerateCode:
    """Test the generate_code function."""

    @patch("hulang.codegen._call_llm")
    def test_passes_system_prompt(self, mock_llm):
        mock_llm.return_value = "int main(){return 0;}"
        generate_code("print hello world")
        args = mock_llm.call_args
        messages = args[0][0]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT
        assert messages[1]["role"] == "user"
        assert "hello world" in messages[1]["content"]

    @patch("hulang.codegen._call_llm")
    def test_returns_code(self, mock_llm):
        mock_llm.return_value = '#include <stdio.h>\nint main(){printf("hi");return 0;}'
        result = generate_code("say hi")
        assert "#include" in result


class TestRepairCode:
    """Test the repair_code function."""

    @patch("hulang.codegen._call_llm")
    def test_includes_errors_and_source(self, mock_llm):
        mock_llm.return_value = "int main(){return 0;}"
        repair_code("bad code", "error: missing semicolon")
        args = mock_llm.call_args
        messages = args[0][0]
        user_msg = messages[1]["content"]
        assert "missing semicolon" in user_msg
        assert "bad code" in user_msg
