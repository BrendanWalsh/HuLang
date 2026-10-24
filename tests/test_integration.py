"""Integration tests -- these actually call the LLM API.

Marked with @pytest.mark.integration so they're skipped by default.
Run with: pytest -m integration
"""

import os
import subprocess
import tempfile

import pytest

from hulang.codegen import generate_code
from hulang.compiler import compile_program


@pytest.mark.integration
class TestLiveCodeGeneration:
    """Tests that call the real LLM API."""

    def test_generates_valid_c(self):
        code = generate_code("Print the numbers 1 to 10, one per line.")
        assert "#include" in code
        assert "main" in code

    def test_compile_hello_world(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "hello.txt")
            with open(src, "w") as f:
                f.write("Print 'Hello, World!' to the screen and exit.")
            out = os.path.join(tmpdir, "hello")
            compile_program(src, output_path=out)

            result = subprocess.run([out], capture_output=True, text=True, timeout=5)
            assert result.returncode == 0
            assert "Hello" in result.stdout

    def test_compile_with_args(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "echo.txt")
            with open(src, "w") as f:
                f.write(
                    "Print all command-line arguments, one per line. "
                    "If no arguments are given, print 'no args'."
                )
            out = os.path.join(tmpdir, "echo")
            compile_program(src, output_path=out)

            result = subprocess.run(
                [out, "foo", "bar"], capture_output=True, text=True, timeout=5
            )
            assert result.returncode == 0
            assert "foo" in result.stdout
            assert "bar" in result.stdout
