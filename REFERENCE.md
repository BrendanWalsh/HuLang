# HuLang Reference

[Back to the README](README.md)

## Installation

```sh
curl -fsSL https://raw.githubusercontent.com/BrendanWalsh/HuLang/main/install.sh | bash && export PATH="$HOME/.local/bin:$PATH"
```

The installer installs HuLang from the repository's `main` branch into an isolated
Python environment under `~/.local/share/hulang`, with `nlc` in `~/.local/bin`.
It installs missing Python and gcc dependencies on Debian/Ubuntu or systems with
Homebrew, and installs Copilot CLI if needed. On other systems, install Python
3.10+ with `venv` and `gcc` before running the script.

If `nlc` is not found afterward, add its directory to your shell's PATH:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Add that line to your shell configuration to keep it across sessions.
Set `HULANG_PREFIX` on the installer process to use a different installation
directory. To install a local checkout, run `HULANG_SOURCE=. bash install.sh`.

The frontend uses a CLI you have already signed into, so there are no API keys
to configure:

| Frontend | One-time setup | Select with |
|----------|----------------|-------------|
| [Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli) | run `copilot` and sign in | nothing -- it is the default |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | install Claude Code, then `claude login` | `-b claude` |

Most examples need only `gcc`. The graphical examples also need SDL2 development
headers; the 3D examples need OpenGL headers as well
(`sudo apt install libsdl2-dev libgl-dev` on Debian/Ubuntu). HuLang detects the
includes and links both libraries automatically.

## Commands

```
nlc build <source.txt> [-o output] [-m model] [-b backend] [-e effort] [--emit-source] [--narrate]
nlc run   <source.txt> [-m model] [-b backend] [--narrate] [-- args...]
nlc emit  <source.txt> [-m model] [-b backend]
nlc models
```

Use `-c 'your program'` (or `--text`) instead of a source file with `build`, `run`,
or `emit`:

```sh
nlc run -c 'Print "Hello, World!" to the screen.'
nlc build -c 'Print "Hello, World!" to the screen.' -o hello
nlc emit -c 'Print "Hello, World!" to the screen.'
nlc run -c 'Print each command-line argument on its own line.' -- one two
```

| Command | What it does |
|---------|--------------|
| `build` | Compile natural language to a native binary |
| `run` | Compile and execute immediately (the binary is temporary) |
| `emit` | Print the generated C to stdout |
| `models` | List available LLM models |

## Flags

| Flag | Description |
|------|-------------|
| `-c, --text` | Inline natural-language source instead of a file |
| `-o, --output` | Output binary path (default: source file basename, or `program` for inline text) |
| `-m, --model` | LLM model (default depends on backend). See `nlc models` |
| `-b, --backend` | CLI backend: `copilot` (default), `claude` |
| `-e, --effort` | Reasoning effort: `low`, `medium`, `high` |
| `-t, --timeout` | Timeout in seconds (default: no limit) |
| `--emit-source` | Save the generated `.c` alongside the binary |
| `--debug` | Compile without optimization (`-O0`) |
| `--narrate` | Generate live stage names and commentary (up to 9 additional model calls) |
| `-v, --verbose` | Show the generated C and the LLM calls |

## Switching models

```sh
nlc build hello.txt -m gpt-5.4-mini             # a specific model
nlc build hello.txt -m claude-sonnet-4.6 -e high
nlc build hello.txt -b claude -m opus
nlc models                                      # backends and their defaults
```

The default model is `auto`, which lets the Copilot CLI choose. To see the
models available to your account, start `copilot` and enter `/model`. Claude
accepts the aliases and full model names shown by `claude --help`.

## Inspecting the intermediate C

HuLang emits C as an intermediate representation. You usually do not need to read
it, but it is available when you want to audit a build, debug a failure, or confirm
what will be handed to `gcc`.

```sh
nlc emit examples/hello.txt
nlc build examples/hello.txt --emit-source
```

Generated C is not a stable source artifact. Different backends, models, or runs
may produce different intermediate code for the same `.txt` input. Pin the backend
and model if you need repeatable builds. If you need bit-for-bit reproducibility,
write C. If you need a native binary from a `.txt` file, continue.
