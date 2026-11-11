#!/bin/bash
# Re-render the README illustrations from the HTML sources.
# Requires Google Chrome or Chromium, and should be run from this directory.
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || true)}"
if [[ -z "$CHROME" ]]; then
  echo "Chrome or Chromium not found" >&2
  exit 1
fi
render() {
  local name="$1" height="$2"
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=2 \
    --window-size=1200,"$height" \
    --default-background-color=EDF3F7 \
    --virtual-time-budget=5000 \
    --screenshot="$(pwd)/${name}.png" \
    "file://$(pwd)/${name}.html"
  echo "wrote ${name}.png"
}
render chat 750
render records 750
render report 750
mkdir -p ../../docs/images
cp chat.png records.png report.png ../../docs/images/
echo "copied PNGs to docs/images/"
