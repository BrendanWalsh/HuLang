"""CLI entry point for the Natural Language Compiler.

Usage:
    nlc build (<source.txt> | -c <text>) [-o output] [-m model] [--emit-source] [--narrate] [-v]
    nlc run   (<source.txt> | -c <text>) [-m model] [--narrate] [-v] [-- args...]
    nlc emit  (<source.txt> | -c <text>) [-m model]
    nlc models
"""

import argparse
import os
import subprocess
import sys
import tempfile

from hulang import __version__
from hulang.codegen import (
    _BACKENDS,
    DEFAULT_BACKEND,
    CodegenError,
    generate_code,
    get_default_model,
    get_sidecar_model,
)
from hulang.compiler import compile_program, read_source

_BACKEND_CHOICES = list(_BACKENDS.keys())


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add flags shared by build/run/emit."""
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("source", nargs="?", help="Natural language source file")
    source.add_argument("-c", "--text", help="Compile natural language directly from this argument")
    parser.add_argument(
        "-m", "--model",
        default=None,
        help="LLM model (default depends on backend). See `nlc models` for options.",
    )
    parser.add_argument(
        "-b", "--backend",
        choices=_BACKEND_CHOICES,
        default=DEFAULT_BACKEND,
        help=f"CLI backend (default: {DEFAULT_BACKEND}). Options: {', '.join(_BACKEND_CHOICES)}",
    )
    parser.add_argument(
        "-e", "--effort",
        choices=["low", "medium", "high"],
        default=None,
        help="Reasoning effort level (supported by claude and copilot backends)",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int, default=None,
        help="Timeout in seconds per LLM call (default: no limit)",
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show generated source and LLM calls")


def _add_narration_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--narrate",
        action="store_true",
        help="generate live stage names and commentary (uses up to 9 additional model calls)",
    )


def cmd_build(args: argparse.Namespace) -> int:
    """Compile a source file or inline text to a native binary."""
    model = args.model or get_default_model(args.backend)
    try:
        compile_program(
            source_path=args.source,
            source_text=args.text,
            output_path=args.output,
            model=model,
            backend=args.backend,
            emit_source=args.emit_source,
            optimization="-O0" if args.debug else "-O2",
            verbose=args.verbose,
            effort=args.effort,
            timeout=args.timeout,
            narrate=args.narrate,
        )
        return 0
    except (FileNotFoundError, ValueError, CodegenError, RuntimeError) as e:
        print(f"\n  💥 {e}", file=sys.stderr)
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Compile to a temp location and execute immediately."""
    model = args.model or get_default_model(args.backend)
    with tempfile.TemporaryDirectory(prefix="hulang_") as tmpdir:
        basename = os.path.splitext(os.path.basename(args.source))[0] if args.source else "program"
        binary = os.path.join(tmpdir, basename)
        try:
            compile_program(
                source_path=args.source,
                source_text=args.text,
                output_path=binary,
                model=model,
                backend=args.backend,
                verbose=args.verbose,
                effort=args.effort,
                timeout=args.timeout,
                narrate=args.narrate,
            )
        except (FileNotFoundError, ValueError, CodegenError, RuntimeError) as e:
            print(f"\n  💥 {e}", file=sys.stderr)
            return 1

        print(f"  {'─' * 40}", file=sys.stderr)
        print(f"  ▶ Running {basename}...\n", file=sys.stderr)

        result = subprocess.run([binary] + args.prog_args)
        return result.returncode


def cmd_emit(args: argparse.Namespace) -> int:
    """Print the generated C code to stdout without compiling."""
    model = args.model or get_default_model(args.backend)
    try:
        source_text = read_source(args.source, args.text)
        code = generate_code(source_text, model=model, backend=args.backend,
                            verbose=args.verbose, effort=args.effort, timeout=args.timeout)
        print(code)
        return 0
    except (FileNotFoundError, ValueError, CodegenError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_models(_args: argparse.Namespace) -> int:
    """Show the available backends and how to pick a model for each."""
    print("HuLang runs the frontend through a CLI you already have.\n")
    print(f"{'BACKEND':<10} {'DEFAULT MODEL':<16} {'NARRATION':<16} SELECT WITH")
    for backend in _BACKEND_CHOICES:
        if backend == "github":
            continue
        print(f"{backend:<10} {get_default_model(backend):<16} "
              f"{get_sidecar_model(backend) or '-':<16} -b {backend}")

    print("\nModel names come from the backend CLI, not from HuLang:")
    print("  copilot  start `copilot`, then enter /model")
    print("  claude   claude --help")
    print("\nUsage: nlc build hello.txt -b copilot -m gpt-5.4-mini")
    print("       nlc build hello.txt -b claude  -m opus")
    print("\nNote: GitHub Models was retired on 2026-07-30, so the 'github' backend")
    print("      no longer works. See https://docs.github.com/en/github-models")
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    """Print version and exit."""
    print(f"nlc (hulang) {__version__}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="nlc",
        description="The Human Language Compiler -- because every other language was just practice",
        epilog="Examples:\n"
               "  nlc build hello.txt                        Compile natural language to a binary\n"
               "  nlc build hello.txt -o greet               Output to ./greet\n"
               "  nlc build hello.txt -m gpt-5.4-mini        Pick a specific model\n"
               "  nlc build hello.txt -b copilot -e high     Copilot with high effort\n"
               "  nlc build hello.txt -b claude -m opus      Use Claude\n"
               "  nlc run hello.txt                          Compile and run immediately\n"
               "  nlc run -c 'Print hello.'                   Compile and run inline text\n"
               "  nlc run hello.txt -- arg1 arg2             Pass args to the compiled program\n"
               "  nlc emit hello.txt                         Just show the generated C code\n"
               "  nlc models                                 List backends and models\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    # build
    p_build = sub.add_parser("build", help="Compile .txt to native binary",
                             description="Compile a natural language source file to a native binary.")
    p_build.add_argument("-o", "--output", help="Output binary path (default: source basename)")
    p_build.add_argument("--emit-source", action="store_true",
                         help="Save the generated .c file alongside the binary")
    p_build.add_argument("--debug", action="store_true",
                         help="Compile without optimization (-O0)")
    _add_common_args(p_build)
    _add_narration_arg(p_build)

    # run
    p_run = sub.add_parser("run", help="Compile and run in one step",
                           description="Compile a natural language source file and execute the result.")
    _add_common_args(p_run)
    p_run.add_argument("prog_args", nargs="*", metavar="ARG",
                       help="Arguments passed to the compiled program (use -- before program options)")
    _add_narration_arg(p_run)

    # emit
    p_emit = sub.add_parser("emit", help="Show the generated C code",
                            description="Generate C code from natural language and print to stdout.")
    _add_common_args(p_emit)

    # models
    sub.add_parser("models", help="List available backends and models",
                   description="Show the frontends HuLang can use and how to pick a model.")

    # version
    sub.add_parser("version", help="Print version")

    argv = sys.argv[1:]
    prog_args = []
    if argv and argv[0] == "run" and "--" in argv:
        separator = argv.index("--")
        prog_args = argv[separator + 1:]
        argv = argv[:separator]
    args = parser.parse_args(argv)
    if args.command == "run":
        args.prog_args += prog_args

    dispatch = {
        "build": cmd_build,
        "run": cmd_run,
        "emit": cmd_emit,
        "models": cmd_models,
        "version": cmd_version,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
