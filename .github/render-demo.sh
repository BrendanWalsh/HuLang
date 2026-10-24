#!/usr/bin/env bash
# Render demo.cast reproducibly into the README GIF and social-video MP4.

set -euo pipefail

cd "$(dirname "$0")/.."

if command -v agg >/dev/null 2>&1; then
    AGG_BIN="$(command -v agg)"
elif [ -x "$HOME/.cargo/bin/agg" ]; then
    AGG_BIN="$HOME/.cargo/bin/agg"
else
    echo "agg not found: https://github.com/asciinema/agg" >&2
    exit 1
fi

for command in curl ffmpeg fc-match; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "$command is required to render the demo" >&2
        exit 1
    fi
done

if ! fc-match --format '%{family}\n' "DejaVu Sans Mono" | grep -qx "DejaVu Sans Mono"; then
    echo "DejaVu Sans Mono is required for the committed 979x649 render" >&2
    exit 1
fi

FONT_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/hulang-demo"
EMOJI_FONT="$FONT_DIR/NotoColorEmoji.ttf"
EMOJI_URL="https://raw.githubusercontent.com/googlefonts/noto-emoji/f3ae03f5e9b3b8516fa151f7168159ca1a3e7515/fonts/NotoColorEmoji.ttf"
EMOJI_SHA256="72a635cb3d2f3524c51620cdde406b217204e8a6a06c6a096ff8ed4b5fd6e27b"

hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | cut -d' ' -f1
    else
        shasum -a 256 "$1" | cut -d' ' -f1
    fi
}

mkdir -p "$FONT_DIR"
if [ ! -f "$EMOJI_FONT" ] || [ "$(hash_file "$EMOJI_FONT")" != "$EMOJI_SHA256" ]; then
    echo "Downloading pinned Noto Color Emoji font..."
    curl --fail --location --silent --show-error "$EMOJI_URL" --output "$EMOJI_FONT"
fi

if [ "$(hash_file "$EMOJI_FONT")" != "$EMOJI_SHA256" ]; then
    echo "Noto Color Emoji checksum mismatch" >&2
    exit 1
fi

"$AGG_BIN" \
    --quiet \
    --renderer resvg \
    --theme github-dark \
    --font-size 16 \
    --line-height 1.4 \
    --speed 1 \
    --idle-time-limit 5 \
    --fps-cap 30 \
    --last-frame-duration 3 \
    --text-font-family "DejaVu Sans Mono" \
    --emoji-font-family "Noto Color Emoji" \
    --font-dir "$FONT_DIR" \
    .github/demo.cast .github/demo.gif

ffmpeg -v error -y \
    -i .github/demo.gif \
    -movflags faststart \
    -pix_fmt yuv420p \
    -vf "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    .github/demo.mp4

echo "Rendered .github/demo.gif and .github/demo.mp4"
