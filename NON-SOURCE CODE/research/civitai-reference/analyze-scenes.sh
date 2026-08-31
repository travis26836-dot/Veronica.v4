#!/usr/bin/env bash
set -euo pipefail

video_path="${1:?usage: analyze-scenes.sh VIDEO_PATH}"

ffmpeg -hide_banner -loglevel info \
  -i "$video_path" \
  -vf "select='gt(scene,0.05)',showinfo" \
  -f null - 2>&1 \
  | grep 'Parsed_showinfo' \
  | sed -n '1,80p'
