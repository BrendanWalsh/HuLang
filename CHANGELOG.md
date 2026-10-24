# Changelog

All notable changes to HuLang will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial release of `nlc` -- the Natural Language Compiler
- `nlc build` -- compile `.txt` to native ELF binary via LLM + gcc
- `nlc run` -- compile and execute in one step
- `nlc emit` -- print generated C source to stdout
- `nlc models` -- show available backends, defaults, and model-selection guidance
- Self-repair: automatic LLM-driven fix when gcc compilation fails (up to 2 retries)
- Auto-linker: detects `#include` directives and adds required library flags
  (OpenSSL, ncurses, SDL2, OpenGL, SQLite, curl, zlib, readline)
- Copilot CLI frontend by default, with Claude Code as an alternative
- Clear migration error for the retired GitHub Models backend
- Configurable LLM model via `--model` flag and backend via `--backend` flag
- Reasoning effort control via `--effort` flag
- No timeout by default (`--timeout` available for opt-in)
- Live animated compilation status; `--narrate` opts into AI-generated stage
  names and sardonic commentary with a bounded additional-call budget
- Cancellation of in-flight narration calls when a build finishes
- Cursor hidden during animation, restored on exit
- 24 example programs covering hello world, fibonacci, snake, raytracer, a
  graphical chess engine, a 3D physics sandbox, a networked procedural world,
  an agentic auto-researcher, todo
  list, in-memory database, C linter, markdown-to-HTML, terminal text editor,
  Conway's Game of Life, a rigged coin flip, a passive-aggressive Magic 8-Ball,
  and more
