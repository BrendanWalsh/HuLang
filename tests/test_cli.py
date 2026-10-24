"""CLI source selection and argument forwarding, without LLM calls."""

from unittest.mock import patch

import pytest

from hulang.cli import main


@pytest.mark.parametrize("command", ["build", "run", "emit"])
@pytest.mark.parametrize("source_args", [[], ["input.txt", "-c", "Print hello."]])
def test_requires_exactly_one_source(monkeypatch, command, source_args):
    monkeypatch.setattr("sys.argv", ["nlc", command, *source_args])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2


@pytest.mark.parametrize("flag", ["-c", "--text"])
def test_inline_build(monkeypatch, flag):
    monkeypatch.setattr("sys.argv", ["nlc", "build", flag, "Print hello.", "-o", "greet"])
    with patch("hulang.cli.compile_program") as compile_mock:
        assert main() == 0
    assert compile_mock.call_args.kwargs["source_path"] is None
    assert compile_mock.call_args.kwargs["source_text"] == "Print hello."
    assert compile_mock.call_args.kwargs["output_path"] == "greet"


@pytest.mark.parametrize("source_args", [["input.txt"], ["-c", "Print the arguments."]])
def test_run_forwards_program_options(monkeypatch, source_args):
    monkeypatch.setattr("sys.argv", ["nlc", "run", *source_args, "--", "-m", "value", "--help"])
    with patch("hulang.cli.compile_program"), patch("hulang.cli.subprocess.run") as run_mock:
        run_mock.return_value.returncode = 7
        assert main() == 7
    assert run_mock.call_args.args[0][1:] == ["-m", "value", "--help"]


@pytest.mark.parametrize("arguments", [["one", "two"], ["-1", "2"]])
def test_run_preserves_file_arguments_without_separator(monkeypatch, arguments):
    monkeypatch.setattr("sys.argv", ["nlc", "run", "input.txt", *arguments])
    with patch("hulang.cli.compile_program"), patch("hulang.cli.subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        assert main() == 0
    assert run_mock.call_args.args[0][1:] == arguments


def test_run_rejects_unknown_compiler_option(monkeypatch):
    monkeypatch.setattr("sys.argv", ["nlc", "run", "-c", "Print hello.", "--typo"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2


@pytest.mark.parametrize("command", ["build", "run", "emit"])
def test_empty_inline_text(monkeypatch, capsys, command):
    monkeypatch.setattr("sys.argv", ["nlc", command, "-c", "  "])
    assert main() == 1
    assert "Source text is empty" in capsys.readouterr().err


def test_inline_emit(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["nlc", "emit", "-c", " Print hello. "])
    with patch("hulang.cli.generate_code", return_value="int main(void) { return 0; }") as gen:
        assert main() == 0
    assert gen.call_args.args == ("Print hello.",)
    assert capsys.readouterr().out == "int main(void) { return 0; }\n"


def test_file_emit(monkeypatch, tmp_path, capsys):
    source = tmp_path / "source.txt"
    source.write_text("Print hello.")
    monkeypatch.setattr("sys.argv", ["nlc", "emit", str(source)])
    with patch("hulang.cli.generate_code", return_value="int main(void) { return 0; }") as gen:
        assert main() == 0
    assert gen.call_args.args == ("Print hello.",)


def test_inline_run_compiles_and_executes(monkeypatch, capfd):
    monkeypatch.setattr("sys.argv", ["nlc", "run", "-c", "Print each argument.", "--", "inline-ok"])
    code = "#include <stdio.h>\nint main(int argc, char **argv) { puts(argv[1]); return 0; }"
    with patch("hulang.compiler.generate_code", return_value=code) as gen:
        assert main() == 0
    assert gen.call_args.args == ("Print each argument.",)
    assert "inline-ok" in capfd.readouterr().out
