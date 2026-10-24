"""Compilation backend -- compiles generated C code with gcc."""

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass

# Map #include headers to required linker flags
_HEADER_TO_LIBS: dict[str, list[str]] = {
    "openssl/md5.h": ["-lssl", "-lcrypto"],
    "openssl/sha.h": ["-lssl", "-lcrypto"],
    "openssl/evp.h": ["-lssl", "-lcrypto"],
    "openssl/aes.h": ["-lssl", "-lcrypto"],
    "curl/curl.h": ["-lcurl"],
    "GL/gl.h": ["-lGL"],
    "ncurses.h": ["-lncurses"],
    "readline/readline.h": ["-lreadline"],
    "SDL2/SDL.h": ["-lSDL2"],
    "sqlite3.h": ["-lsqlite3"],
    "zlib.h": ["-lz"],
}


def _detect_libraries(source_code: str) -> list[str]:
    """Scan #include directives and return needed linker flags."""
    libs: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r'#include\s*[<"]([^>"]+)[>"]', source_code):
        header = match.group(1)
        for pattern, flags in _HEADER_TO_LIBS.items():
            if header == pattern or header.startswith(pattern.split("/")[0] + "/"):
                for flag in flags:
                    if flag not in seen:
                        libs.append(flag)
                        seen.add(flag)
    return libs


@dataclass
class CompileResult:
    success: bool
    output_path: str | None
    errors: str
    warnings: str


def compile_c(
    source_code: str,
    output_path: str,
    optimization: str = "-O2",
    keep_source: str | None = None,
) -> CompileResult:
    """Compile C source code to a native binary.

    Args:
        source_code: The C source code string.
        output_path: Path for the output binary.
        optimization: gcc optimization flag.
        keep_source: If set, save the .c source to this path.
    """
    # Write source to a temp file (or the keep path)
    if keep_source:
        source_path = keep_source
        with open(source_path, "w") as f:
            f.write(source_code)
    else:
        fd, source_path = tempfile.mkstemp(suffix=".c", prefix="hulang_")
        os.close(fd)
        with open(source_path, "w") as f:
            f.write(source_code)

    try:
        extra_libs = _detect_libraries(source_code)
        result = subprocess.run(
            [
                "gcc",
                "-Wall", "-Wextra", "-Wno-deprecated-declarations",
                optimization,
                "-std=c11",
                "-D_POSIX_C_SOURCE=200809L",
                "-o", output_path,
                source_path,
                "-lm",          # math library
                "-lpthread",    # threading (commonly needed)
                *extra_libs,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        stderr = result.stderr.strip()
        if result.returncode != 0:
            # On failure, pass full stderr as errors for better repair context
            return CompileResult(
                success=False,
                output_path=None,
                errors=stderr,
                warnings="",
            )

        # On success, everything in stderr is warnings
        return CompileResult(
            success=True,
            output_path=output_path,
            errors="",
            warnings=stderr,
        )
    except subprocess.TimeoutExpired:
        return CompileResult(
            success=False,
            output_path=None,
            errors="Compilation timed out (30s limit)",
            warnings="",
        )
    finally:
        if not keep_source and os.path.exists(source_path):
            os.unlink(source_path)
