#!/usr/bin/env bash
set -euo pipefail

DATE="${1:-$(date +%F)}"

python3 scripts/collect.py --date "$DATE"
python3 scripts/score.py --date "$DATE"
python3 scripts/build_specs.py --date "$DATE"
python3 scripts/audit_pipeline.py --date "$DATE"
python3 scripts/render_daily.py --date "$DATE"
python3 scripts/qc.py --date "$DATE"
python3 scripts/send_telegram.py --date "$DATE" --dry-run
