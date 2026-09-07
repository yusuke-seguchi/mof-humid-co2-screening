#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
office_fonts='/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts'
font_dir="$PWD/report_build/local_fonts"
mkdir -p "$font_dir"
cp "$office_fonts/meiryo.ttc" "$office_fonts/meiryob.ttc" "$font_dir/"
test -f "$font_dir/meiryo.ttc"
test -f "$font_dir/meiryob.ttc"
run_marp() {
  docker run --rm --init \
    -v "$PWD:/home/marp/app" \
    -v "$font_dir/meiryo.ttc:/usr/share/fonts/truetype/meiryo.ttc:ro" \
    -v "$font_dir/meiryob.ttc:/usr/share/fonts/truetype/meiryob.ttc:ro" \
    marpteam/marp-cli:latest "$@"
}
docker run --rm \
  -v "$font_dir/meiryo.ttc:/usr/share/fonts/truetype/meiryo.ttc:ro" \
  -v "$font_dir/meiryob.ttc:/usr/share/fonts/truetype/meiryob.ttc:ro" \
  --entrypoint fc-match marpteam/marp-cli:latest Meiryo
run_marp mof_screening_report.md --pptx --allow-local-files -o mof_screening_report_meiryo.pptx
run_marp mof_screening_report.md --images png --allow-local-files -o report_build/meiryo.png
