#!/usr/bin/env bash
# 動画を読み取り用のコンタクトシートに変換する。
# 使い方: scripts/video-sheet.sh <動画ファイル> [出力先ディレクトリ]
#
# 出力:
#   <出力先>/meta.txt        尺・解像度・fps・音量
#   <出力先>/sheet_1s.jpg    全体の流れ(1秒ごと。40秒を超える動画は自動で間引く)
#   <出力先>/sheet_head.jpg  冒頭2秒を8分割(フックの確認用)
#   <出力先>/sheet_tail.jpg  ラスト3秒を8分割(オチ・CTAの確認用)
set -euo pipefail

SRC="${1:?動画ファイルを指定してください}"
OUT="${2:-${TMPDIR:-/tmp}/video-sheet-$(date +%s)}"
mkdir -p "$OUT"

# ffmpeg を探す。無ければ pip の imageio-ffmpeg に積まれたバイナリを使う。
if command -v ffmpeg >/dev/null 2>&1; then
  FF="$(command -v ffmpeg)"
else
  if ! python3 -c "import imageio_ffmpeg" >/dev/null 2>&1; then
    echo "ffmpeg が無いので imageio-ffmpeg を入れます…" >&2
    pip3 install --quiet imageio-ffmpeg >/dev/null
  fi
  FF="$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
fi

# ffmpeg は出力ファイル無しだと終了コード1を返すので、pipefail 対策に || true を付ける
DUR="$({ "$FF" -hide_banner -i "$SRC" 2>&1 || true; } | sed -n 's/.*Duration: \([0-9:.]*\).*/\1/p' | head -1)"
if [ -z "$DUR" ]; then
  echo "動画の尺を読み取れませんでした: $SRC" >&2
  exit 1
fi
SEC="$(python3 -c "h,m,s='${DUR}'.split(':'); print(float(h)*3600+float(m)*60+float(s))")"

{
  echo "ファイル: $SRC"
  { "$FF" -hide_banner -i "$SRC" 2>&1 || true; } | grep -E "Duration|Stream #" || true
  { "$FF" -hide_banner -i "$SRC" -af volumedetect -f null /dev/null 2>&1 || true; } | grep -E "mean_volume|max_volume" || true
} > "$OUT/meta.txt"

# 全体。尺に合わせてコマ数と行数を決める(最大40コマ。長い動画は間引く)
read -r FPS ROWS <<EOF
$(python3 -c "
import math
sec = ${SEC}
cols, cap = 5, 40
fps = min(1.0, cap / max(sec, 1))
n = min(cap, max(1, math.ceil(sec * fps)))
print(round(fps, 3), math.ceil(n / cols))
")
EOF
"$FF" -hide_banner -loglevel error -i "$SRC" \
  -vf "fps=${FPS},scale=320:-1,tile=5x${ROWS}:margin=6:padding=6" -frames:v 1 -q:v 3 "$OUT/sheet_1s.jpg"

# 冒頭2秒(フック)
"$FF" -hide_banner -loglevel error -ss 0 -t 2 -i "$SRC" \
  -vf "fps=4,scale=260:-1,tile=4x2:margin=5:padding=5" -frames:v 1 -q:v 3 "$OUT/sheet_head.jpg"

# ラスト3秒(オチ・CTA)
TAIL="$(python3 -c "print(max(0, ${SEC}-3))")"
"$FF" -hide_banner -loglevel error -ss "$TAIL" -i "$SRC" \
  -vf "fps=3,scale=260:-1,tile=5x2:margin=5:padding=5" -frames:v 1 -q:v 3 "$OUT/sheet_tail.jpg"

echo "$OUT"
