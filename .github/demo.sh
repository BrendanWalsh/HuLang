#!/usr/bin/env bash
# Demo script for recording the HuLang GIF.
# Records a real `nlc build` so the animated status (spinner + AI-generated
# stages + sardonic commentary) appears in the GIF.

set -e

cd "$(dirname "$0")/.."

# Frontend used for the recording. Override to record with a specific model:
#   HULANG_BACKEND=copilot HULANG_MODEL=gpt-5.4-mini bash .github/demo.sh
BACKEND="${HULANG_BACKEND:-copilot}"
MODEL="${HULANG_MODEL:-}"
printf -v BUILD_CMD 'python3 nlc build examples/text_editor.txt -o ed -b %q' "$BACKEND"
if [ -n "$MODEL" ]; then
    printf -v QUOTED_MODEL '%q' "$MODEL"
    BUILD_CMD="$BUILD_CMD -m $QUOTED_MODEL"
fi
BUILD_CMD="$BUILD_CMD --narrate"

type_slow() {
    local text="$1"
    local delay="${2:-0.035}"
    for ((i=0; i<${#text}; i++)); do
        printf '%s' "${text:$i:1}"
        sleep "$delay"
    done
}

run_cmd() {
    local cmd="$1"
    printf '\033[1;32m$\033[0m '
    type_slow "$cmd" 0.035
    sleep 0.25
    printf '\n'
    eval "$cmd"
}

clear
printf '\033[1;36m'
echo "  HuLang -- the human language compiler"
printf '\033[0m'
printf '\033[2m  .txt → native binary, via LLM + gcc\033[0m\n'
echo ""
sleep 0.8

printf '\033[1;33m# Ask for a terminal text editor in natural language:\033[0m\n'
sleep 0.4
run_cmd "cat examples/text_editor.txt"
sleep 1.4

echo ""
printf '\033[1;33m# Compile it:\033[0m\n'
sleep 0.4
run_cmd "$BUILD_CMD"
sleep 1.0

echo ""
printf '\033[1;33m# It is, in fact, a real binary:\033[0m\n'
sleep 0.4
run_cmd "file ed"
sleep 1.0
run_cmd "ls -lh ed"
sleep 2.0

rm -f ed
