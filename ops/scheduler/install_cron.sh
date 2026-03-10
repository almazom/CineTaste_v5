#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNNER="$ROOT/ops/scheduler/run_pipeline.sh"
CRON_SHELL="/bin/bash"
CRON_PATH="/home/pets/.local/bin:/home/pets/.npm-global/bin:/usr/local/bin:/usr/bin:/bin"
CRON_INTERVAL="${CINETASTE_CRON_INTERVAL:-*/15 * * * *}"
MODE="${1:-production}"

if [[ ! -x "$RUNNER" ]]; then
    echo "Runner is missing or not executable: $RUNNER" >&2
    exit 1
fi

case "$MODE" in
    production)
        cron_command="$RUNNER"
        ;;
    dry-run)
        cron_command="CINETASTE_SCHEDULE_MODE=dry-run $RUNNER"
        ;;
    *)
        echo "Usage: $0 [production|dry-run]" >&2
        exit 2
        ;;
esac

current_cron="$(mktemp)"
next_cron="$(mktemp)"
cleanup() {
    rm -f "$current_cron" "$next_cron"
}
trap cleanup EXIT

if ! crontab -l > "$current_cron" 2>/dev/null; then
    : > "$current_cron"
fi

awk '
BEGIN { skip=0 }
$0 == "# === CINETASTE V5 SCHEDULER START ===" { skip=1; next }
$0 == "# === CINETASTE V5 SCHEDULER END ===" { skip=0; next }
skip { next }
$0 ~ /CineTaste v5 — Full pipeline every 15 minutes/ { next }
$0 ~ /ID: v5-every-15min/ { next }
$0 ~ /\*\/15 \* \* \* \* .*CineTaste_v5.*(\.\/run|ops\/scheduler\/run_pipeline\.sh)/ { next }
{ print }
' "$current_cron" > "$next_cron"

{
    echo
    echo "# === CINETASTE V5 SCHEDULER START ==="
    echo "# CineTaste v5 — managed by ops/scheduler/install_cron.sh"
    echo "SHELL=$CRON_SHELL"
    echo "PATH=$CRON_PATH"
    echo "MAILTO=\"\""
    echo "$CRON_INTERVAL $cron_command"
    echo "# === CINETASTE V5 SCHEDULER END ==="
} >> "$next_cron"

if crontab -n "$next_cron" >/dev/null 2>&1; then
    :
else
    echo "crontab -n validation failed for generated schedule" >&2
    exit 3
fi

crontab "$next_cron"
crontab -l
