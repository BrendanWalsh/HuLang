# Contributing to HuLang

Thanks for your interest in contributing to HuLang! This project is an experiment
in treating natural language as a programming language, and contributions of all
kinds are welcome.

## Ways to Contribute

- **Example programs** — Write interesting `.txt` programs and submit them to `examples/`
- **Prompt engineering** — Improve the system prompts in `hulang/prompts.py` to
  produce better, more reliable C code
- **Backend improvements** — Better auto-linking, support for additional compilers
  (clang, MSVC), or additional target languages
- **Bug reports** — If a reasonable `.txt` program fails to compile, open an issue
  with the source text and error output
- **Documentation** — Improve README, add tutorials, write about interesting findings

## Development Setup

The repository includes a devcontainer with Python 3.12, GCC, SDL2/OpenGL
headers, GitHub CLI, and GitHub Copilot CLI. In VS Code, run
**Dev Containers: Reopen in Container**, or open the repository in Codespaces.
The container installs HuLang and its development dependencies automatically.

For a local setup:

```bash
# Clone the repo
git clone https://github.com/BrendanWalsh/HuLang.git
cd HuLang

# Install in development mode with test/lint dependencies
make dev
# or: pip install -e ".[dev]"

# Run tests (unit tests only, no API calls)
make test

# Run linter
make lint
```

## Prerequisites

- Python 3.10+
- `gcc` installed and on PATH
- One frontend CLI signed in: `copilot` (default) or `claude`
- SDL2 development headers for graphical examples, plus OpenGL headers for the
  3D examples (`libsdl2-dev libgl-dev` on Debian/Ubuntu)

## Running Tests

```bash
# Unit tests only (fast, no API calls)
make test

# All tests including integration (calls LLM API — costs tokens)
make test-all
```

## Code Style

- We use [Ruff](https://docs.astral.sh/ruff/) for linting
- Max line length: 100 characters
- Type hints are encouraged but not required
- Run `make lint-fix` to auto-fix style issues before submitting

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b my-feature`)
3. Make your changes
4. Run `make lint && make test` to verify
5. Commit with a clear message
6. Open a Pull Request

## Adding Examples

Example programs live in `examples/`. A good example:

- Does something interesting or useful
- Is written in clear natural language
- Compiles successfully with `nlc build`
- Demonstrates a capability (file I/O, algorithms, data structures, etc.)

Test your example before submitting:
```bash
nlc build examples/my_example.txt --emit-source
./my_example  # verify it works
```

## Project Structure

```
HuLang/
├── nlc                     # CLI entry point (run directly or pip install)
├── hulang/
│   ├── __init__.py         # Package metadata
│   ├── cli.py              # Argument parsing and command dispatch
│   ├── compiler.py         # Compilation pipeline orchestrator
│   ├── codegen.py          # LLM backends (Copilot, Claude)
│   ├── backend.py          # gcc backend + auto-linker
│   ├── prompts.py          # Frontend prompts
│   └── status.py           # Animated status + commentary
├── examples/               # Example .txt programs
├── tests/                  # Unit + integration tests
├── .github/
│   ├── workflows/ci.yml    # CI pipeline
│   ├── pipeline.svg        # Pipeline diagram used in the README
│   ├── timeline.svg        # Abstraction timeline used in the README
│   ├── chess-engine.png    # Generated SDL2 chess interface
│   ├── physics-sandbox.png # Generated OpenGL physics scene
│   ├── networked-world.png # Generated OpenGL network world
│   ├── auto-researcher-result.png # Replicated research result
│   ├── demo.sh             # Runs the recorded compilation
│   ├── render-demo.sh      # Reproducibly renders the GIF and MP4
│   └── ISSUE_TEMPLATE/     # Bug reports and feature requests
├── pyproject.toml          # Package configuration
├── Makefile                # Dev shortcuts
├── LICENSE                 # MIT
├── CONTRIBUTING.md         # How to contribute
└── CHANGELOG.md            # Release history
```

## Architecture Overview

```
User writes program.txt (natural language)
        │
        ▼
┌─ codegen.py ──────────────────────────┐
│  Sends text + system prompt to LLM    │
│  Receives C source code               │
│  Strips markdown fences if present    │
└───────────────────────────────────────┘
        │
        ▼
┌─ backend.py ──────────────────────────┐
│  Auto-detects needed libraries        │
│  Compiles with gcc                    │
│  Returns success/failure + errors     │
└───────────────────────────────────────┘
        │
        ▼  (if compilation fails)
┌─ codegen.py (repair) ────────────────┐
│  Sends code + errors back to LLM     │
│  Gets corrected code                  │
│  Retries compilation (up to 2x)       │
└───────────────────────────────────────┘
        │
        ▼
   Native binary ✅
```

## Maintainer Notes

### Re-recording the demo GIF

The demo GIF records HuLang compiling `examples/human_language_compiler.txt`,
then uses that generated compiler to compile and run another program. Both
compilation stages are live; generated C is not hand-edited. The script uses
a temporary directory and removes its outputs when it exits. To re-record:

```bash
asciinema rec .github/demo.cast --cols 100 --rows 28 \
    --command "bash .github/demo.sh" --overwrite
.github/render-demo.sh
```

Requires `asciinema`, [`agg`](https://github.com/asciinema/agg), `ffmpeg`,
`fontconfig`, DejaVu Sans Mono, and `curl`, plus a signed-in frontend CLI. The
demo script honours
`HULANG_BACKEND`, `HULANG_MODEL`, and `HULANG_EFFORT`, so record with a specific
model and effort like this:

```bash
HULANG_BACKEND=copilot HULANG_MODEL=gpt-5.6-luna HULANG_EFFORT=low \
    asciinema rec .github/demo.cast --cols 100 --rows 28 \
        --command "bash .github/demo.sh" --overwrite
```

The demo defaults to Copilot CLI with `gpt-5.6-luna` at low reasoning effort.
The generated compiler also uses `gpt-5.6-luna` at low effort, as specified in
its natural-language source, regardless of the outer compiler's settings.

The demo passes `--narrate`, which opts into up to nine additional model calls
for the stage names and commentary. Ordinary builds do not make those cosmetic
calls. Narration needs a TTY, which `asciinema` provides.

`render-demo.sh` pins the renderer, timing, frame rate, font families, and emoji
font checksum. Those details matter: agg's current defaults differ from the
version that produced the original 979x649 GIF, and ffmpeg otherwise converts
GIF centiseconds into a wasteful 100 fps MP4.

### Regenerating the social preview

GitHub shows a 1280x640 OG card whenever the repo URL is shared. To
regenerate:

```bash
python3 .github/generate_social_preview.py
```

Then upload the resulting `.github/social-preview.png` via
**Settings → Social preview** in the repo (the file lives in the repo
for archival, but GitHub stores its own copy when you upload).

## Questions?

Open an issue or start a discussion — happy to help!
