"""LLM-based code generation — the compiler frontend.

Shells out to CLI tools for LLM calls — zero auth management.
Supported CLIs:
  copilot  -- copilot -p (GitHub Copilot CLI agent mode, default)
  claude   -- claude -p (Anthropic Claude Code CLI)

The `github` backend used GitHub Models, which GitHub fully retired on
2026-07-30. It is kept in the registry only to give a clear error.
"""

import os
import subprocess
import sys
import tempfile
import threading
import time

from .prompts import REPAIR_PROMPT, SYSTEM_PROMPT


class CodegenError(Exception):
    pass


def _strip_fences(content: str) -> str:
    """Remove markdown code fences if the LLM wraps its output."""
    if content.startswith("```"):
        lines = content.split("\n")
        lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        return "\n".join(lines)
    return content


def _stop_process(process: subprocess.Popen) -> tuple[str, str]:
    """Terminate a cancellable model call and collect its output."""
    process.terminate()
    try:
        return process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        return process.communicate()


def _run_cli(
    cmd: list[str],
    stdin: str,
    verbose: bool = False,
    timeout: int | None = None,
    cancel_event: threading.Event | None = None,
) -> str:
    """Run a CLI command, return stdout, raise CodegenError on failure."""
    if verbose:
        print(f"  ⟶ {' '.join(cmd[:5])}...", file=sys.stderr)

    if cancel_event is None:
        try:
            result = subprocess.run(
                cmd, input=stdin, capture_output=True, text=True, timeout=timeout,
            )
        except FileNotFoundError as e:
            raise CodegenError(f"CLI not found: {cmd[0]}") from e
        except subprocess.TimeoutExpired as e:
            raise CodegenError(f"Model timed out ({timeout}s limit).") from e
        stdout = result.stdout
        stderr = result.stderr
        returncode = result.returncode
    else:
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError as e:
            raise CodegenError(f"CLI not found: {cmd[0]}") from e

        deadline = time.monotonic() + timeout if timeout is not None else None
        pending_input: str | None = stdin
        while True:
            try:
                stdout, stderr = process.communicate(input=pending_input, timeout=0.1)
                break
            except subprocess.TimeoutExpired:
                pending_input = None
                if cancel_event.is_set():
                    _stop_process(process)
                    raise CodegenError("Model call cancelled.") from None
                if deadline is not None and time.monotonic() >= deadline:
                    _stop_process(process)
                    raise CodegenError(f"Model timed out ({timeout}s limit).") from None
        returncode = process.returncode

    if returncode != 0:
        raise CodegenError(
            stderr.strip() or f"{cmd[0]} exited with code {returncode}"
        )

    return _strip_fences(stdout.strip())


def _split_messages(messages: list[dict]) -> tuple[str, str]:
    """Extract system and user content from message list."""
    system_msg = ""
    user_msg = ""
    for m in messages:
        if m["role"] == "system":
            system_msg = m["content"]
        elif m["role"] == "user":
            user_msg = m["content"]
    return system_msg, user_msg


GITHUB_MODELS_RETIRED = (
    "The 'github' backend used GitHub Models, which GitHub fully retired on\n"
    "2026-07-30 (https://docs.github.com/en/github-models).\n"
    "Pick a frontend that still exists:\n"
    "  nlc build <source.txt> -b copilot\n"
    "  nlc build <source.txt> -b claude"
)


def _call_github(
    messages: list[dict], model: str, verbose: bool = False,
    effort: str | None = None, timeout: int | None = None,
) -> str:
    """GitHub Models was retired on 2026-07-30; fail with a migration path."""
    raise CodegenError(GITHUB_MODELS_RETIRED)


def _call_claude(
    messages: list[dict], model: str, verbose: bool = False,
    effort: str | None = None, timeout: int | None = None,
) -> str:
    """Call via `claude -p`."""
    system_msg, user_msg = _split_messages(messages)
    cmd = [
        "claude", "-p",
        "--model", model,
        "--output-format", "text",
        "--append-system-prompt", system_msg,
    ]
    if effort:
        cmd += ["--effort", effort]
    cmd.append(user_msg)
    try:
        return _run_cli(cmd, "", verbose, timeout=timeout)
    except CodegenError as e:
        if "CLI not found" in str(e):
            raise CodegenError(
                "Claude CLI not found. Install it:\n"
                "  https://docs.anthropic.com/en/docs/claude-code"
            ) from e
        raise


def _call_copilot(
    messages: list[dict], model: str, verbose: bool = False,
    effort: str | None = None, timeout: int | None = None,
) -> str:
    """Call via `copilot -p` -- lets the agent write the C file directly."""
    system_msg, user_msg = _split_messages(messages)
    fd, outfile = tempfile.mkstemp(suffix=".c", prefix="hulang_copilot_")
    os.close(fd)
    os.unlink(outfile)  # let copilot create it

    full_prompt = (
        "Implement the program described below by writing a C source file with your "
        "file-editing tools. Do not just print the code in your response.\n\n"
        "The code-generation rules apply to the contents of the file, not to your "
        "tool calls or final response.\n"
        f"<code-generation-rules>\n{system_msg}\n</code-generation-rules>\n\n"
        f"<program-description>\n{user_msg}\n</program-description>\n\n"
        "The output path below is an artifact of this compilation. It is not a "
        "requirement of the program and must not be embedded in the generated code.\n"
        f"Use your file-editing tools to save the C source code to {outfile}"
    )
    cmd = [
        "copilot", "-p", full_prompt,
        "--model", model,
        "--add-dir", os.path.dirname(outfile),
        "--allow-all-tools", "--allow-all-paths",
    ]
    if effort:
        cmd += ["--reasoning-effort", effort]
    try:
        _run_cli(cmd, "", verbose, timeout=timeout)
    except CodegenError as e:
        # Clean up partial file on error
        if os.path.exists(outfile):
            os.unlink(outfile)
        if "CLI not found" in str(e):
            raise CodegenError(
                "Copilot CLI not found. Install it:\n"
                "  https://docs.github.com/en/copilot/github-copilot-in-the-cli"
            ) from e
        raise

    if not os.path.isfile(outfile):
        raise CodegenError("Copilot did not produce a C source file.")

    try:
        with open(outfile) as f:
            return f.read()
    finally:
        os.unlink(outfile)


# Backend registry
_BACKENDS = {
    "copilot": _call_copilot,
    "claude": _call_claude,
    "github": _call_github,
}

_DEFAULT_MODELS = {
    "claude": "sonnet",
    "copilot": "auto",
}

# Small, cheap models used for the live status narration, which fires
# repeatedly during a build and never needs to be clever.
_SIDECAR_MODELS = {
    "claude": "haiku",
    "copilot": "gpt-5.4-mini",
}

DEFAULT_BACKEND = "copilot"


def get_default_model(backend: str) -> str:
    """Return the default model for a backend."""
    return _DEFAULT_MODELS.get(backend, "auto")


def get_sidecar_model(backend: str) -> str | None:
    """Return the fast model used for status narration, or None if unsupported."""
    return _SIDECAR_MODELS.get(backend)


def _text_copilot(
    prompt: str,
    model: str,
    timeout: int | None,
    cancel_event: threading.Event | None = None,
) -> str:
    """Plain-text answer from `copilot -p`, with no tool access."""
    return _run_cli(
        ["copilot", "-p", prompt, "--model", model, "-s", "--no-color"],
        "", timeout=timeout, cancel_event=cancel_event,
    )


def _text_claude(
    prompt: str,
    model: str,
    timeout: int | None,
    cancel_event: threading.Event | None = None,
) -> str:
    """Plain-text answer from `claude -p`."""
    return _run_cli(
        ["claude", "-p", "--model", model, "--output-format", "text", prompt],
        "", timeout=timeout, cancel_event=cancel_event,
    )


_TEXT_BACKENDS = {
    "copilot": _text_copilot,
    "claude": _text_claude,
}


def complete_text(
    prompt: str,
    backend: str = DEFAULT_BACKEND,
    model: str | None = None,
    timeout: int | None = None,
    cancel_event: threading.Event | None = None,
) -> str:
    """Ask a backend for a short plain-text answer.

    Used by the live status narration, which wants prose rather than C and
    must never be granted tool access. Raises CodegenError on any failure so
    callers can degrade quietly.
    """
    fn = _TEXT_BACKENDS.get(backend)
    if not fn:
        raise CodegenError(f"Backend '{backend}' cannot answer plain-text prompts.")
    return fn(
        prompt,
        model or get_sidecar_model(backend) or get_default_model(backend),
        timeout,
        cancel_event,
    )


def _call_llm(
    messages: list[dict],
    model: str,
    backend: str = DEFAULT_BACKEND,
    verbose: bool = False,
    effort: str | None = None,
    timeout: int | None = None,
) -> str:
    """Route to the appropriate CLI backend."""
    fn = _BACKENDS.get(backend)
    if not fn:
        raise CodegenError(
            f"Unknown backend '{backend}'. Options: {', '.join(_BACKENDS)}"
        )
    return fn(messages, model, verbose=verbose, effort=effort, timeout=timeout)


def generate_code(
    source_text: str,
    model: str | None = None,
    backend: str = DEFAULT_BACKEND,
    verbose: bool = False,
    effort: str | None = None,
    timeout: int | None = None,
) -> str:
    """Generate C code from natural language description."""
    model = model or get_default_model(backend)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": source_text},
    ]
    return _call_llm(messages, model, backend, verbose, effort, timeout)


def repair_code(
    source: str,
    errors: str,
    model: str | None = None,
    backend: str = DEFAULT_BACKEND,
    verbose: bool = False,
    effort: str | None = None,
    timeout: int | None = None,
) -> str:
    """Attempt to fix compilation errors via LLM."""
    model = model or get_default_model(backend)
    prompt = REPAIR_PROMPT.format(errors=errors, source=source)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    return _call_llm(messages, model, backend, verbose, effort, timeout)
