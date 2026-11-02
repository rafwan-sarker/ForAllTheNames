#!/bin/bash
# Definition of done: pipeline scripts compile, web app type-checks and builds.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m py_compile pipeline/*.py
cd web && npm run build --silent
echo "verify: ok"
