#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$ROOT/logs"
TEMP_DIR="$ROOT/temp"
LOCK_FILE="$TEMP_DIR/cinetaste-scheduler.lock"
LOG_FILE="${CINETASTE_SCHEDULER_LOG:-$LOG_DIR/scheduler.log}"
STATUS_FILE="${CINETASTE_SCHEDULER_STATUS_LOG:-$LOG_DIR/scheduler-status.log}"
MODE="${CINETASTE_SCHEDULE_MODE:-production}"

mkdir -p "$LOG_DIR" "$TEMP_DIR"

export PATH="/home/pets/.local/bin:/home/pets/.npm-global/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    printf '=== [%s] scheduler skip reason=lock-held pid=%s ===\n' "$(date -Iseconds)" "$$" >> "$LOG_FILE"
    printf '%s | skip | reason=lock-held | pid=%s\n' "$(date -Iseconds)" "$$" >> "$STATUS_FILE"
    exit 0
fi

exec >> "$LOG_FILE" 2>&1

echo
echo "=== [$(date -Iseconds)] scheduler start mode=$MODE pid=$$ ==="

if [[ -f "$ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT/.env"
    set +a
fi

cd "$ROOT"

run_args=()
case "$MODE" in
    production)
        ;;
    dry-run)
        run_args+=(--dry-run)
        ;;
    *)
        echo "Unsupported CINETASTE_SCHEDULE_MODE=$MODE"
        printf '%s | fail | exit=2 | mode=%s | reason=invalid-mode\n' "$(date -Iseconds)" "$MODE" >> "$STATUS_FILE"
        exit 2
        ;;
esac

if [[ -n "${CINETASTE_SCHEDULE_WHEN:-}" ]]; then
    run_args+=(--when "$CINETASTE_SCHEDULE_WHEN")
fi

set +e
"$ROOT/run" "${run_args[@]}"
exit_code=$?
set -e

if [[ $exit_code -eq 0 ]]; then
    echo "=== [$(date -Iseconds)] scheduler success exit=$exit_code mode=$MODE ==="
    printf '%s | success | exit=%s | mode=%s\n' "$(date -Iseconds)" "$exit_code" "$MODE" >> "$STATUS_FILE"
else
    echo "=== [$(date -Iseconds)] scheduler fail exit=$exit_code mode=$MODE ==="
    printf '%s | fail | exit=%s | mode=%s\n' "$(date -Iseconds)" "$exit_code" "$MODE" >> "$STATUS_FILE"
fi

exit "$exit_code"
