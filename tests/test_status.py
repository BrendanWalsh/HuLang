"""Tests for the live status sidecar.

These exercise the timing / threading behavior with mocked LLM calls so they're
deterministic and fast.
"""

import threading
import time
from unittest.mock import patch

from hulang import status
from hulang.codegen import CodegenError


def _make_status_no_tty(source: str = "do a thing"):
    """Build a LiveStatus instance and force-enable the threads even without a TTY."""
    s = status.LiveStatus(source, narrate=True)
    s._tty = True  # let start() actually launch the threads
    return s


def test_commentary_fires_even_when_stages_cycle():
    """Regression: stages cycling should NOT prevent commentary from firing.

    Original bug: commentary required 15s of stage-staleness, but the animator
    cycles stages every N seconds, so the staleness counter reset and commentary
    never fired.  Fix uses a steady time-based cadence instead.

    We assert by counting how many times _generate_commentary was invoked --
    not by inspecting _comment, because _animate clears _comment on stage change
    (which is the intended UX) and would race with our assertion.
    """
    s = _make_status_no_tty("compile a fibonacci")
    # Override timing so the test runs fast
    s._FIRST_COMMENT_DELAY = 0.1
    s._REPEAT_COMMENT_DELAY = 0.5
    s._STAGE_INTERVAL = 0.1  # cycle stages aggressively to trigger the old bug
    s._COMMENTARY_TICK = 0.05  # fast loop tick for fast tests

    fake_stages = ["parsing intent", "lowering to C", "linking", "shipping"]
    call_count = {"n": 0}

    def fake_commentary(*_args, **_kwargs):
        call_count["n"] += 1
        return "just gave up on bounds checking"

    with patch("hulang.status._generate_stages", return_value=fake_stages), \
         patch("hulang.status._generate_commentary", side_effect=fake_commentary):
        s.start()
        try:
            time.sleep(1.5)
            assert call_count["n"] >= 1, (
                "commentary never fired despite >1s elapsed and rapid stage cycling; "
                "this is the regression we're guarding against"
            )
        finally:
            s.stop()


def test_commentary_repeats():
    """After the first comment, more should arrive on the repeat cadence."""
    s = _make_status_no_tty("count primes")
    s._FIRST_COMMENT_DELAY = 0.05
    s._REPEAT_COMMENT_DELAY = 0.2
    s._STAGE_INTERVAL = 10.0  # don't cycle stages, focus on commentary cadence
    s._COMMENTARY_TICK = 0.05

    call_count = {"n": 0}

    def fake_commentary(*_args, **_kwargs):
        call_count["n"] += 1
        return f"comment #{call_count['n']}"

    with patch("hulang.status._generate_stages", return_value=["only stage"]), \
         patch("hulang.status._generate_commentary", side_effect=fake_commentary):
        s.start()
        try:
            time.sleep(1.5)  # 0.05 + 0.2 * N -- expect ~7 calls but we just need >=2
            assert call_count["n"] >= 2, (
                f"expected at least 2 commentary calls in 1.5s, got {call_count['n']}"
            )
        finally:
            s.stop()


def test_commentary_skipped_when_llm_unavailable():
    """When _generate_commentary returns None, the loop must not crash and
    must keep trying on the cadence rather than spinning."""
    s = _make_status_no_tty("nothing")
    s._FIRST_COMMENT_DELAY = 0.05
    s._REPEAT_COMMENT_DELAY = 0.1
    s._STAGE_INTERVAL = 10.0
    s._COMMENTARY_TICK = 0.05

    call_count = {"n": 0}

    def fake_commentary(*_args, **_kwargs):
        call_count["n"] += 1
        return None  # simulate LLM unavailable

    with patch("hulang.status._generate_stages", return_value=["only stage"]), \
         patch("hulang.status._generate_commentary", side_effect=fake_commentary):
        s.start()
        try:
            time.sleep(1.0)
            assert call_count["n"] >= 2, "should keep retrying when LLM is unavailable"
            assert s._comment is None, "no comment should be set when LLM returns None"
        finally:
            s.stop()


def test_narration_is_opt_in():
    """Ordinary builds must not spend additional model calls for cosmetics."""
    s = status.LiveStatus("anything")
    s._tty = True
    s.start()
    try:
        assert s._thread is not None
        assert s._sidecar_thread is None
        assert s._commentary_thread is None
    finally:
        s.stop()


def test_commentary_call_budget():
    """Even explicit narration has a hard upper bound on model calls."""
    s = _make_status_no_tty("count primes")
    s._FIRST_COMMENT_DELAY = 0.01
    s._REPEAT_COMMENT_DELAY = 0.01
    s._STAGE_INTERVAL = 10.0
    s._COMMENTARY_TICK = 0.01
    s._MAX_COMMENTARY_CALLS = 3

    call_count = {"n": 0}

    def fake_commentary(*_args, **_kwargs):
        call_count["n"] += 1
        return f"comment #{call_count['n']}"

    with patch("hulang.status._generate_stages", return_value=["only stage"]), \
         patch("hulang.status._generate_commentary", side_effect=fake_commentary):
        s.start()
        try:
            time.sleep(0.25)
            assert call_count["n"] == 3
        finally:
            s.stop()


def test_stop_cancels_and_joins_sidecar_calls():
    """A short build must not leave a billable narration process behind."""
    started = threading.Event()

    def blocking_completion(*_args, cancel_event=None, **_kwargs):
        started.set()
        assert cancel_event is not None
        cancel_event.wait(5)
        raise CodegenError("Model call cancelled.")

    s = _make_status_no_tty("finish quickly")
    with patch("hulang.status.complete_text", side_effect=blocking_completion):
        s.start()
        assert started.wait(1)
        s.stop()

    assert s._sidecar_thread is not None
    assert not s._sidecar_thread.is_alive()
    assert s._commentary_thread is not None
    assert not s._commentary_thread.is_alive()


def test_no_op_when_not_a_tty(monkeypatch):
    """In non-TTY environments (e.g. CI logs), start() should be a no-op."""
    s = status.LiveStatus("anything")
    s._tty = False
    s.start()
    assert s._thread is None
    assert s._sidecar_thread is None
    assert s._commentary_thread is None
    s.stop()  # must not crash
