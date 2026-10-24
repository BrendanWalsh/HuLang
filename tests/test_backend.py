"""Tests for the gcc compilation backend."""

import os
import stat
import tempfile

from hulang.backend import _detect_libraries, compile_c


class TestDetectLibraries:
    """Test auto-detection of linker flags from #include directives."""

    def test_no_special_includes(self):
        code = '#include <stdio.h>\n#include <stdlib.h>\nint main(){return 0;}'
        assert _detect_libraries(code) == []

    def test_openssl_md5(self):
        code = '#include <openssl/md5.h>\nint main(){return 0;}'
        libs = _detect_libraries(code)
        assert "-lssl" in libs
        assert "-lcrypto" in libs

    def test_openssl_evp(self):
        code = '#include <openssl/evp.h>\nint main(){return 0;}'
        libs = _detect_libraries(code)
        assert "-lssl" in libs
        assert "-lcrypto" in libs

    def test_curl(self):
        code = '#include <curl/curl.h>\nint main(){return 0;}'
        assert "-lcurl" in _detect_libraries(code)

    def test_opengl(self):
        code = '#include <GL/gl.h>\nint main(){return 0;}'
        assert "-lGL" in _detect_libraries(code)

    def test_ncurses(self):
        code = '#include <ncurses.h>\nint main(){return 0;}'
        assert "-lncurses" in _detect_libraries(code)

    def test_sqlite(self):
        code = '#include <sqlite3.h>\nint main(){return 0;}'
        assert "-lsqlite3" in _detect_libraries(code)

    def test_sdl2(self):
        code = '#include <SDL2/SDL.h>\nint main(){return 0;}'
        assert "-lSDL2" in _detect_libraries(code)

    def test_zlib(self):
        code = '#include <zlib.h>\nint main(){return 0;}'
        assert "-lz" in _detect_libraries(code)

    def test_multiple_libraries(self):
        code = '#include <openssl/md5.h>\n#include <curl/curl.h>\nint main(){return 0;}'
        libs = _detect_libraries(code)
        assert "-lssl" in libs
        assert "-lcrypto" in libs
        assert "-lcurl" in libs

    def test_no_duplicates(self):
        code = '#include <openssl/md5.h>\n#include <openssl/sha.h>\nint main(){return 0;}'
        libs = _detect_libraries(code)
        assert libs.count("-lssl") == 1
        assert libs.count("-lcrypto") == 1

    def test_quoted_includes(self):
        code = '#include "sqlite3.h"\nint main(){return 0;}'
        assert "-lsqlite3" in _detect_libraries(code)


class TestCompileC:
    """Test the gcc compilation wrapper."""

    def test_simple_program(self):
        code = '#include <stdio.h>\nint main(){printf("hello\\n");return 0;}'
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "test_bin")
            result = compile_c(code, out)
            assert result.success
            assert result.output_path == out
            assert os.path.isfile(out)
            assert os.stat(out).st_mode & stat.S_IXUSR  # executable

    def test_compile_error(self):
        code = "this is not C code at all"
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "test_bin")
            result = compile_c(code, out)
            assert not result.success
            assert result.output_path is None
            assert result.errors  # should have error text

    def test_keep_source(self):
        code = '#include <stdio.h>\nint main(){printf("hi\\n");return 0;}'
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "test_bin")
            src = os.path.join(tmpdir, "test.c")
            result = compile_c(code, out, keep_source=src)
            assert result.success
            assert os.path.isfile(src)
            with open(src) as f:
                assert f.read() == code

    def test_math_library_linked(self):
        code = (
            '#include <stdio.h>\n#include <math.h>\n'
            'int main(){printf("%f\\n",sqrt(2.0));return 0;}'
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "test_bin")
            result = compile_c(code, out)
            assert result.success

    def test_optimization_flag(self):
        code = '#include <stdio.h>\nint main(){return 0;}'
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "test_bin")
            result = compile_c(code, out, optimization="-O0")
            assert result.success

    def test_posix_features(self):
        code = (
            '#include <stdio.h>\n#include <sys/types.h>\n'
            'int main(){ssize_t x = 0; (void)x; return 0;}'
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "test_bin")
            result = compile_c(code, out)
            assert result.success
