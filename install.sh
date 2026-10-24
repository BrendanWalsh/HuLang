#!/usr/bin/env bash
set -euo pipefail

fail() {
    printf 'HuLang: %s\n' "$*" >&2
    exit 1
}

prefix="${HULANG_PREFIX:-$HOME/.local}"
venv="$prefix/share/hulang/venv"
source="${HULANG_SOURCE:-https://github.com/BrendanWalsh/HuLang/archive/refs/heads/main.zip}"
export PATH="$prefix/bin:$PATH"

has_python() {
    command -v python3 >/dev/null 2>&1 &&
        python3 -c 'import ensurepip, venv, sys; sys.exit(sys.version_info < (3, 10))'
}

if ! has_python || ! command -v gcc >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
        sudo_cmd=()
        if [ "$(id -u)" -ne 0 ]; then
            command -v sudo >/dev/null 2>&1 || fail "Install Python 3.10+, python3-venv and gcc, then rerun."
            sudo_cmd=(sudo)
        fi
        "${sudo_cmd[@]}" apt-get update -qq
        "${sudo_cmd[@]}" apt-get install -y -qq python3 python3-venv gcc
    elif command -v brew >/dev/null 2>&1; then
        brew install python gcc
    else
        fail "Install Python 3.10+ (with venv) and gcc, then rerun this installer."
    fi
fi

has_python || fail "Python 3.10+ with venv is required."
command -v gcc >/dev/null 2>&1 || fail "gcc is required."
command -v curl >/dev/null 2>&1 || fail "curl is required."

mkdir -p "$prefix/bin"
if [ -e "$prefix/bin/nlc" ] || [ -L "$prefix/bin/nlc" ]; then
    if [ ! -L "$prefix/bin/nlc" ] || [ "$(readlink "$prefix/bin/nlc")" != "$venv/bin/nlc" ]; then
        fail "$prefix/bin/nlc already exists and is not managed by this installer."
    fi
fi

python3 -m venv "$venv"
"$venv/bin/python" -m pip install --quiet --upgrade "$source"
ln -sfn "$venv/bin/nlc" "$prefix/bin/nlc"

if ! command -v copilot >/dev/null 2>&1; then
    curl -fsSL https://gh.io/copilot-install | PREFIX="$prefix" bash
    printf '\nRun copilot and sign in before compiling your first program.\n'
fi

"$prefix/bin/nlc" --version
printf '\nInstalled. If nlc is not on your shell PATH, run:\n'
printf '  export PATH="%s/bin:$PATH"\n' "$prefix"
