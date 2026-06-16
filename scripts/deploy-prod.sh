#!/bin/bash
# Деплой на прод: https://192-210-213-135.sslip.io
# Использование: bash scripts/deploy-prod.sh [BRANCH]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export BRANCH="${1:-main}"
exec bash "$SCRIPT_DIR/remote-deploy.sh"
