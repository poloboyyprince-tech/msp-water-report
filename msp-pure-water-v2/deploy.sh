#!/bin/bash
# Deploy MSP Pure Water to production (GitHub Pages repo poloboyyprince-tech/msppurewaterco.com).
# Builds to dist-prod, syncs into a persistent clone at prod-repo/, commits, pushes.
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py --out dist-prod --production >/dev/null
if [ ! -d prod-repo/.git ]; then
  rm -rf prod-repo
  git clone -q https://github.com/poloboyyprince-tech/msppurewaterco.com.git prod-repo
fi
cd prod-repo
git fetch -q origin && git reset -q --hard origin/main
rsync -a --delete --exclude .git ../dist-prod/ ./
git add -A
if git diff --cached --quiet; then echo "production already up to date"; exit 0; fi
git -c user.name="MSP Pure Water" -c user.email="info@msppurewaterco.com" commit -q -m "${1:-Deploy $(date +%F\ %H:%M)}"
git push -q origin main
echo "production pushed: $(git rev-parse --short HEAD)"
