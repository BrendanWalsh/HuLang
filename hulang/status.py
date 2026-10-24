"""Live compilation status — animation + sidecar model for contextual updates.

The narration runs on whichever backend the build is using, via a small,
cheap model. If that backend cannot answer, the animation degrades to a
plain spinner rather than failing the build.
"""

import sys
import threading
import time

from .codegen import DEFAULT_BACKEND, CodegenError, complete_text

# Braille spinner frames
_SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# Agent CLIs are slower than a raw completions endpoint, so these are generous.
_STAGE_TIMEOUT = 45
_COMMENT_TIMEOUT = 30

_ANSI_DIM = "\033[2m"
_ANSI_CYAN = "\033[36m"
_ANSI_YELLOW = "\033[33m"
_ANSI_RESET = "\033[0m"
_ANSI_CLEAR_LINE = "\033[2K\r"


def _generate_stages(
    source_text: str,
    backend: str = DEFAULT_BACKEND,
    model: str | None = None,
    cancel_event: threading.Event | None = None,
) -> list[str]:
    """Ask a fast model to generate contextual compilation stages."""
    prompt = (
        "Output only the stage names, one per line. Nothing else.\n\n"
        "You are narrating the compilation stages of a natural language compiler. "
        "Given this program description, generate exactly 20 short (3-6 word) compilation "
        "stage descriptions that sound technical but relate to what the program actually does. "
        "Be creative and specific to the program content. Cover the full journey from "
        "understanding the request through code generation to final output. "
        "No numbering, one per line, no quotes.\n"
        "Example for a fibonacci program:\n"
        "parsing mathematical intent\n"
        "resolving recursive structure\n"
        "analyzing sequence boundaries\n"
        "mapping overflow conditions\n"
        "generating loop constructs\n"
        "optimizing register allocation\n\n"
        f"Program:\n{source_text[:500]}"
    )
    try:
        out = complete_text(
            prompt,
            backend=backend,
            model=model,
            timeout=_STAGE_TIMEOUT,
            cancel_event=cancel_event,
        )
    except CodegenError:
        return []
    stages = [s.strip() for s in out.strip().split("\n") if s.strip()]
    return stages[:20]


def _generate_commentary(
    stage: str, elapsed: int, program_summary: str,
    backend: str = DEFAULT_BACKEND, model: str | None = None,
    cancel_event: threading.Event | None = None,
) -> str | None:
    """Ask a fast model for sardonic narration of what the AI is actually doing."""
    prompt = (
        "You're a sardonic narrator describing an AI's internal struggles while "
        "writing code. Be specific and technical but funny. One line only. No quotes. "
        "No emoji. Lowercase.\n\n"
        f"A natural language compiler is turning this source text into C code:\n"
        f"'{program_summary}'\n\n"
        f"It's been on the '{stage}' phase for {elapsed} seconds total.\n\n"
        "Write ONE short sardonic narration (under 70 chars) of what the AI is "
        "probably actually doing right now — describe the internal reasoning process "
        "in a funny, specific way. Think about what decisions a programmer would be "
        "wrestling with at this compilation stage for this specific program.\n\n"
        "IMPORTANT: Do NOT start with or heavily use 'pondering', 'wondering', "
        "'wrestling', 'struggling', 'debating', or 'realizing'. "
        "Never repeat a previous remark's structure. "
        "Vary your sentence structure. Some options:\n"
        "- describe an action: 'just deleted the entire hash table implementation'\n"
        "- state a realization: 'turns out SQL parsing is basically a PhD thesis'\n"
        "- report a status: 'on its third rewrite of the tokenizer'\n"
        "- make an observation: 'the malloc/free ratio is getting concerning'\n"
        "- admit defeat: 'gave up on proper error messages, using printf instead'"
    )
    try:
        out = complete_text(
            prompt,
            backend=backend,
            model=model,
            timeout=_COMMENT_TIMEOUT,
            cancel_event=cancel_event,
        )
    except CodegenError:
        return None
    line = out.strip().split("\n")[0].strip() if out.strip() else ""
    return line[:80] or None


_ANSI_HIDE_CURSOR = "\033[?25l"
_ANSI_SHOW_CURSOR = "\033[?25h"
_ANSI_UP = "\033[A"


class LiveStatus:
    """Animated status display with contextual stage updates and idle commentary."""

    # Timing constants (class-level so tests can override).
    _FIRST_COMMENT_DELAY = 12.0
    _REPEAT_COMMENT_DELAY = 14.0
    _STAGE_INTERVAL = 22.0
    _COMMENTARY_TICK = 0.5  # how often the commentary loop wakes up to check
    _MAX_COMMENTARY_CALLS = 8

    def __init__(self, source_text: str, backend: str = DEFAULT_BACKEND,
                 model: str | None = None, narrate: bool = False,
                 fallback_stage: str = "generating C"):
        self._source_text = source_text
        self._backend = backend
        self._model = model
        self._narrate = narrate
        self._fallback_stage = fallback_stage
        self._stages: list[str] = []
        self._current_stage = 0
        self._running = False
        self._thread: threading.Thread | None = None
        self._sidecar_thread: threading.Thread | None = None
        self._commentary_thread: threading.Thread | None = None
        self._stage_lock = threading.Lock()
        self._comment: str | None = None
        self._comment_expire = 0.0
        self._comments: list[str] = []  # comments for current stage
        self._displayed_lines = 0  # how many lines we've written (spinner + comments)
        self._start_time = 0.0
        self._stop_event = threading.Event()
        self._tty = sys.stderr.isatty()

    def start(self) -> None:
        """Start the animation and sidecar model."""
        if not self._tty:
            return
        self._stop_event.clear()
        self._running = True
        self._start_time = time.time()
        sys.stderr.write(_ANSI_HIDE_CURSOR)
        sys.stderr.flush()
        if self._narrate:
            self._sidecar_thread = threading.Thread(target=self._run_sidecar, daemon=True)
            self._sidecar_thread.start()
            self._commentary_thread = threading.Thread(target=self._run_commentary, daemon=True)
            self._commentary_thread.start()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the animation and clear all displayed lines."""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        if self._sidecar_thread:
            self._sidecar_thread.join(timeout=3)
        if self._commentary_thread:
            self._commentary_thread.join(timeout=3)
        if self._tty:
            self._clear_block()
            sys.stderr.write(_ANSI_SHOW_CURSOR)
            sys.stderr.flush()

    def _clear_block(self) -> None:
        """Erase the spinner line and all comment lines below it."""
        # Move up to the spinner line, clearing each line on the way
        for _ in range(self._displayed_lines):
            sys.stderr.write(f"{_ANSI_CLEAR_LINE}{_ANSI_UP}")
        sys.stderr.write(_ANSI_CLEAR_LINE)
        sys.stderr.flush()
        self._displayed_lines = 0

    def _run_sidecar(self) -> None:
        """Generate contextual stages via fast model."""
        stages = _generate_stages(
            self._source_text,
            self._backend,
            self._model,
            self._stop_event,
        )
        with self._stage_lock:
            if self._running and not self._stop_event.is_set():
                self._stages = stages

    def _run_commentary(self) -> None:
        """Periodically generate witty remarks on a steady cadence."""
        # Time-based cadence: first commentary at FIRST_COMMENT_DELAY elapsed,
        # then every REPEAT_COMMENT_DELAY.  We don't tie this to stage staleness
        # because stages auto-cycle, which would prevent commentary from ever firing.
        next_fire = self._start_time + self._FIRST_COMMENT_DELAY
        calls = 0

        while self._running and calls < self._MAX_COMMENTARY_CALLS:
            if self._stop_event.wait(self._COMMENTARY_TICK):
                break
            if not self._running:
                break

            now = time.time()
            if now < next_fire:
                continue

            with self._stage_lock:
                if self._stages:
                    current = self._stages[min(self._current_stage, len(self._stages) - 1)]
                else:
                    current = "initializing"

            elapsed = int(now - self._start_time)
            calls += 1
            comment = _generate_commentary(current, elapsed, self._source_text[:200],
                                           self._backend, self._model, self._stop_event)
            if not self._running or self._stop_event.is_set():
                break
            if comment:
                with self._stage_lock:
                    self._comment = comment
                    self._comment_expire = now + 30  # show until cleared
                next_fire = time.time() + self._REPEAT_COMMENT_DELAY
            else:
                # LLM unavailable or returned nothing -- back off but keep trying
                next_fire = now + self._REPEAT_COMMENT_DELAY

    def _animate(self) -> None:
        """Render spinner line + stacking comments. Clear all when stage changes."""
        frame = 0
        last_stage_time = time.time()
        stage_interval = self._STAGE_INTERVAL
        prev_stage_idx = -1

        while self._running:
            elapsed = time.time() - self._start_time
            spinner = _SPINNER[frame % len(_SPINNER)]

            # Advance stage periodically
            if time.time() - last_stage_time > stage_interval:
                with self._stage_lock:
                    if self._stages:
                        self._current_stage = (self._current_stage + 1) % len(self._stages)
                last_stage_time = time.time()

            with self._stage_lock:
                stage_idx = self._current_stage
                if self._stages:
                    stage = self._stages[stage_idx]
                    stage_text = f"{_ANSI_CYAN}{stage}{_ANSI_RESET}"
                else:
                    stage_text = f"{_ANSI_DIM}{self._fallback_stage}{_ANSI_RESET}"

                # Collect new comment if available
                new_comment = None
                if (self._comment
                        and time.time() < self._comment_expire
                        and self._comment not in self._comments):
                    new_comment = self._comment

            # Stage changed -- clear the whole block and reset comments
            if stage_idx != prev_stage_idx and prev_stage_idx >= 0:
                self._clear_block()
                with self._stage_lock:
                    self._comments.clear()
                    self._comment = None
            prev_stage_idx = stage_idx

            # If there's a new comment, clear block and redraw with all comments
            if new_comment:
                self._clear_block()
                with self._stage_lock:
                    self._comments.append(new_comment)

            # Redraw: move cursor up to overwrite existing block
            if self._displayed_lines > 0:
                sys.stderr.write("\r")
                for _ in range(self._displayed_lines):
                    sys.stderr.write(f"{_ANSI_UP}")

            # Write spinner line
            time_str = f"{_ANSI_DIM}{elapsed:.0f}s{_ANSI_RESET}"
            spinner_line = f"  {_ANSI_YELLOW}{spinner}{_ANSI_RESET} {stage_text} {time_str}"
            sys.stderr.write(f"{_ANSI_CLEAR_LINE}{spinner_line}")

            # Write comment lines
            with self._stage_lock:
                comments = list(self._comments)
            for c in comments:
                sys.stderr.write(f"\n{_ANSI_CLEAR_LINE}     {_ANSI_DIM}└ {c}{_ANSI_RESET}")

            self._displayed_lines = len(comments)  # lines below the spinner
            sys.stderr.flush()

            frame += 1
            time.sleep(0.1)
