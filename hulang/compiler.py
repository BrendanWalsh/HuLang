"""Main compiler pipeline -- ties frontend (LLM) to backend (gcc)."""

import os
import sys
import time

from .backend import CompileResult, compile_c
from .codegen import (
    DEFAULT_BACKEND,
    CodegenError,
    generate_code,
    get_default_model,
    repair_code,
)
from .status import LiveStatus

# ANSI colors
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_RESET = "\033[0m"


def _status(icon: str, msg: str) -> None:
    print(f"  {icon} {msg}", file=sys.stderr)


def read_source(source_path: str | None, source_text: str | None = None) -> str:
    if (source_path is None) == (source_text is None):
        raise ValueError("Provide either a source file or inline text with --text")
    if source_path is not None:
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        with open(source_path) as f:
            source_text = f.read()
    if source_text is None or not source_text.strip():
        raise ValueError("Source file is empty" if source_path is not None else "Source text is empty")
    return source_text.strip()


def compile_program(
    source_path: str | None = None,
    output_path: str | None = None,
    model: str | None = None,
    backend: str = DEFAULT_BACKEND,
    emit_source: bool = False,
    optimization: str = "-O2",
    max_retries: int = 2,
    verbose: bool = False,
    effort: str | None = None,
    timeout: int | None = None,
    narrate: bool = False,
    source_text: str | None = None,
) -> str:
    """Full compilation pipeline: source file or inline text → LLM → gcc → binary.

    Returns the path to the compiled binary.
    Raises on failure.
    """
    # 1. Read source
    model = model or get_default_model(backend)

    source_text = read_source(source_path, source_text)
    basename = os.path.splitext(os.path.basename(source_path))[0] if source_path else "program"
    if not output_path:
        output_path = os.path.join(os.path.dirname(source_path or "") or ".", basename)

    source_out = f"{output_path}.c" if emit_source else None

    print(file=sys.stderr)
    print(f"  {_BOLD}hulang{_RESET} {_DIM}the human language compiler{_RESET}", file=sys.stderr)
    print(f"  {_DIM}{'─' * 40}{_RESET}", file=sys.stderr)
    _status("📄", f"source: {_CYAN}{source_path or '<inline>'}{_RESET}")
    _status("🎯", f"output: {_CYAN}{output_path}{_RESET}")
    _status("🧠", f"model:  {model}")
    print(file=sys.stderr)

    # 2. Generate code via LLM
    status = LiveStatus(source_text, backend=backend, narrate=narrate)
    status.start()
    t0 = time.time()

    try:
        c_code = generate_code(source_text, model=model, backend=backend, verbose=verbose,
                               effort=effort, timeout=timeout)
    except CodegenError as e:
        raise CodegenError(f"code generation failed: {e}") from e
    finally:
        status.stop()

    gen_time = time.time() - t0
    lines = c_code.count("\n") + 1
    _status("✓", f"{_GREEN}generated {lines} lines of C in {gen_time:.1f}s{_RESET}")

    if verbose:
        print(f"\n{_DIM}{'─' * 40}{_RESET}", file=sys.stderr)
        print(c_code, file=sys.stderr)
        print(f"{_DIM}{'─' * 40}{_RESET}\n", file=sys.stderr)

    # 3. Compile with gcc (with retry loop for self-healing)
    for attempt in range(1 + max_retries):
        _status("🔨", "compiling C → native binary ..." if attempt == 0
                else f"retry {attempt}/{max_retries} after repair ...")

        t1 = time.time()
        result: CompileResult = compile_c(
            c_code,
            output_path,
            optimization=optimization,
            keep_source=source_out,
        )
        compile_time = time.time() - t1

        if result.success:
            _status("✓", f"{_GREEN}compiled in {compile_time:.1f}s{_RESET}")
            if result.warnings:
                _status("⚠", f"{_YELLOW}warnings:{_RESET}")
                for w in result.warnings.split("\n")[:5]:
                    print(f"      {_DIM}{w}{_RESET}", file=sys.stderr)
            break
        else:
            _status("✗", f"{_RED}compilation failed{_RESET}")
            if verbose or attempt == max_retries:
                for e in result.errors.split("\n")[:10]:
                    print(f"      {_DIM}{e}{_RESET}", file=sys.stderr)

            if attempt < max_retries:
                _status("🔧", f"{_YELLOW}repairing...{_RESET}")
                repair_status = LiveStatus("Fix compilation errors:\n" + result.errors[:500],
                                           backend=backend, fallback_stage="repairing C")
                repair_status.start()
                try:
                    c_code = repair_code(
                        c_code, result.errors, model=model, backend=backend,
                        verbose=verbose, effort=effort, timeout=timeout,
                    )
                    repair_lines = c_code.count("\n") + 1
                    _status("✓", f"{_GREEN}repaired ({repair_lines} lines){_RESET}")
                except CodegenError as e:
                    raise CodegenError(f"repair failed: {e}") from e
                finally:
                    repair_status.stop()
            else:
                raise RuntimeError(
                    f"Compilation failed after {max_retries} repair attempts.\n"
                    f"Errors:\n{result.errors}"
                )

    # 4. Final output
    binary_size = os.path.getsize(output_path)
    size_str = (
        f"{binary_size / 1024:.1f} KB" if binary_size < 1024 * 1024
        else f"{binary_size / (1024 * 1024):.1f} MB"
    )

    print(file=sys.stderr)
    _status("✅", f"{_GREEN}{_BOLD}Build succeeded{_RESET}")
    _status("📦", f"binary: {_CYAN}{output_path}{_RESET} ({size_str})")
    if source_out:
        _status("📝", f"source: {_CYAN}{source_out}{_RESET}")
    print(file=sys.stderr)

    return output_path
