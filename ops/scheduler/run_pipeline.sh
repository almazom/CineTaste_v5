#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$ROOT/logs"
TEMP_DIR="$ROOT/temp"
LOCK_FILE="$TEMP_DIR/cinetaste-scheduler.lock"
LOG_FILE="${CINETASTE_SCHEDULER_LOG:-$LOG_DIR/scheduler.log}"
STATUS_FILE="${CINETASTE_SCHEDULER_STATUS_LOG:-$LOG_DIR/scheduler-status.log}"
MODE="${CINETASTE_SCHEDULE_MODE:-production}"
MAX_ATTEMPTS="${CINETASTE_SCHEDULER_MAX_ATTEMPTS:-3}"
RETRY_DELAY_SECONDS="${CINETASTE_SCHEDULER_RETRY_DELAY_SECONDS:-180}"
RETRY_EXIT_CODES="${CINETASTE_SCHEDULER_RETRY_EXIT_CODES:-69}"

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

should_retry_exit() {
    local exit_code="$1"
    local item
    for item in ${RETRY_EXIT_CODES//,/ }; do
        [[ "$exit_code" == "$item" ]] && return 0
    done
    return 1
}

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

attempt=1
exit_code=0

while true; do
    echo "=== [$(date -Iseconds)] scheduler pipeline attempt=${attempt}/${MAX_ATTEMPTS} mode=$MODE ==="

    set +e
    "$ROOT/run" "${run_args[@]}"
    exit_code=$?
    set -e

    if [[ $exit_code -eq 0 ]]; then
        break
    fi

    if [[ "$attempt" -ge "$MAX_ATTEMPTS" ]] || ! should_retry_exit "$exit_code"; then
        break
    fi

    echo "=== [$(date -Iseconds)] scheduler retry exit=$exit_code delay=${RETRY_DELAY_SECONDS}s next_attempt=$((attempt + 1)) ==="
    printf '%s | retry | exit=%s | mode=%s | attempt=%s/%s | sleep=%s\n' \
        "$(date -Iseconds)" "$exit_code" "$MODE" "$attempt" "$MAX_ATTEMPTS" "$RETRY_DELAY_SECONDS" >> "$STATUS_FILE"
    sleep "$RETRY_DELAY_SECONDS"
    attempt=$((attempt + 1))
done

if [[ $exit_code -eq 0 ]]; then
    echo "=== [$(date -Iseconds)] scheduler success exit=$exit_code mode=$MODE ==="
    printf '%s | success | exit=%s | mode=%s | attempts=%s\n' "$(date -Iseconds)" "$exit_code" "$MODE" "$attempt" >> "$STATUS_FILE"
else
    echo "=== [$(date -Iseconds)] scheduler fail exit=$exit_code mode=$MODE ==="
    printf '%s | fail | exit=%s | mode=%s | attempts=%s\n' "$(date -Iseconds)" "$exit_code" "$MODE" "$attempt" >> "$STATUS_FILE"
fi

exit "$exit_code"
