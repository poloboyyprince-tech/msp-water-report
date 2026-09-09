#!/usr/bin/env bash
# Rebuilds the whole static site from the mirrored Amboras pages in ./pages
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py           # 17 pages converted from the Amboras mirror
python3 gen.py             # 22 pages that were 404s on the original site
python3 gen_products.py    # 4 client-rendered product pages, rebuilt from catalog data
python3 gen_schedule.py    # client-rendered scheduler, rebuilt as a static wizard
echo "Build complete."
