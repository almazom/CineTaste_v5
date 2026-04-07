# Scheduler Hardening

## Current Rule

Keep the `crontab` entry minimal and move shell logic into a versioned wrapper script:

```cron
*/15 * * * * /home/pets/zoo/CineTaste_v5/ops/scheduler/run_pipeline.sh
```

The managed installer is:

```bash
./ops/scheduler/install_cron.sh
```

## Why the previous inline cron was brittle

- `crontab` treats unescaped `%` as a newline boundary, so `$(date '+%Y-%m-%d %H:%M:%S %Z')` breaks the command.
- Long inline shell pipelines are hard to review, test, and update safely.
- Cron launches a sparse shell environment, so relying on interactive profile state is fragile.
- Overlapping runs are easy to trigger if one pipeline execution takes longer than the schedule interval.

## Bulletproof Practices

- Keep `crontab` to one absolute-path command.
- Set `SHELL`, `PATH`, and `MAILTO` explicitly.
- Load `.env` inside the wrapper script instead of depending on login shells.
- Use `flock` to skip overlapping runs cleanly.
- Log start/end markers and exit codes from the wrapper.
- Validate generated crontabs with the local cron dry-run mode before installing (`crontab -n` on this host).
- Prefer `systemd timer` with `Persistent=true` when catch-up after downtime is required and the host is prepared for it.

## Repo Files

- `ops/scheduler/run_pipeline.sh`: scheduler wrapper with env loading, locking, and logging
- `ops/scheduler/install_cron.sh`: installs the managed cron block
- `logs/scheduler.log`: full scheduled execution log
- `logs/scheduler-status.log`: compact scheduler outcomes

## Retry Policy

The scheduler wrapper can retry source-unavailable pipeline exits before giving up.

Environment variables:

- `CINETASTE_SCHEDULER_MAX_ATTEMPTS` default `3`
- `CINETASTE_SCHEDULER_RETRY_DELAY_SECONDS` default `180`
- `CINETASTE_SCHEDULER_RETRY_EXIT_CODES` default `69`

Current intent:

- `69` means upstream/source unavailable
- the wrapper retries those exits with delay
- non-retryable failures still stop immediately

## Verification

Dry-run the scheduler wrapper without sending live Telegram messages:

```bash
CINETASTE_SCHEDULE_MODE=dry-run ./ops/scheduler/run_pipeline.sh
```

Install the production schedule:

```bash
./ops/scheduler/install_cron.sh
```

Install a dry-run schedule:

```bash
./ops/scheduler/install_cron.sh dry-run
```
