"""Tests for the full compilation pipeline."""

import os
from unittest.mock import patch

import pytest

from hulang.codegen import CodegenError
from hulang.compiler import compile_program

HELLO_C = '#include <stdio.h>\nint main(){printf("hello from hulang\\n");return 0;}'


class TestCompileProgram:
    """Test the full pipeline: read .txt → LLM → gcc → binary."""

    @patch("hulang.compiler.generate_code")
    def test_full_pipeline(self, mock_gen, tmp_path):
        mock_gen.return_value = HELLO_C

        src = tmp_path / "hello.txt"
        src.write_text("print hello from hulang")
        out = str(tmp_path / "hello")

        result = compile_program(str(src), output_path=out)
        assert result == out
        assert os.path.isfile(out)
        assert os.access(out, os.X_OK)

    @patch("hulang.compiler.generate_code")
    def test_emit_source(self, mock_gen, tmp_path):
        mock_gen.return_value = HELLO_C

        src = tmp_path / "prog.txt"
        src.write_text("a program")
        out = str(tmp_path / "prog")

        compile_program(str(src), output_path=out, emit_source=True)
        assert os.path.isfile(out + ".c")
        with open(out + ".c") as f:
            assert "#include" in f.read()

    @patch("hulang.compiler.generate_code")
    @patch("hulang.compiler.repair_code")
    def test_self_repair(self, mock_repair, mock_gen, tmp_path):
        # First generation has a bug, repair fixes it
        mock_gen.return_value = "int main(){undeclared_var = 1; return 0;}"
        mock_repair.return_value = HELLO_C

        src = tmp_path / "test.txt"
        src.write_text("a program")
        out = str(tmp_path / "test")

        result = compile_program(str(src), output_path=out)
        assert os.path.isfile(result)
        mock_repair.assert_called_once()

    def test_missing_source_file(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            compile_program("/nonexistent/file.txt")

    def test_empty_source_file(self, tmp_path):
        src = tmp_path / "empty.txt"
        src.write_text("")
        with pytest.raises(ValueError, match="empty"):
            compile_program(str(src))

    @patch("hulang.compiler.generate_code")
    def test_inline_default_output(self, mock_gen, tmp_path, monkeypatch):
        mock_gen.return_value = HELLO_C
        monkeypatch.chdir(tmp_path)
        result = compile_program(source_text="Print hello.", emit_source=True)
        assert result == "./program"
        assert (tmp_path / "program").is_file()
        assert (tmp_path / "program.c").read_text() == HELLO_C
        mock_gen.assert_called_once()
        assert mock_gen.call_args.args == ("Print hello.",)

    def test_rejects_both_source_forms(self, tmp_path):
        with pytest.raises(ValueError, match="either"):
            compile_program(str(tmp_path / "input.txt"), source_text="Print hello.")

    @patch("hulang.compiler.generate_code")
    def test_default_output_path(self, mock_gen, tmp_path):
        mock_gen.return_value = HELLO_C

        src = tmp_path / "myprogram.txt"
        src.write_text("do something")

        result = compile_program(str(src))
        assert os.path.basename(result) == "myprogram"
        # Cleanup
        if os.path.exists(result):
            os.unlink(result)

    @patch("hulang.compiler.generate_code")
    def test_all_retries_exhausted(self, mock_gen, tmp_path):
        mock_gen.return_value = "completely invalid {{ not C at all }}"

        src = tmp_path / "bad.txt"
        src.write_text("something")
        out = str(tmp_path / "bad")

        with pytest.raises(RuntimeError, match="Compilation failed"):
            compile_program(str(src), output_path=out, max_retries=0)

    @patch("hulang.compiler.generate_code", side_effect=CodegenError("API down"))
    def test_codegen_error_propagates(self, _mock_gen, tmp_path):
        src = tmp_path / "err.txt"
        src.write_text("do something")
        with pytest.raises(CodegenError, match="API down"):
            compile_program(str(src))

    @patch("hulang.compiler.LiveStatus")
    @patch("hulang.compiler.generate_code")
    def test_narration_is_forwarded_to_status(self, mock_gen, mock_status, tmp_path):
        mock_gen.return_value = HELLO_C
        src = tmp_path / "narrated.txt"
        src.write_text("say hello")

        compile_program(str(src), output_path=str(tmp_path / "narrated"), narrate=True)

        mock_status.assert_called_once_with(
            "say hello",
            backend="copilot",
            narrate=True,
        )
