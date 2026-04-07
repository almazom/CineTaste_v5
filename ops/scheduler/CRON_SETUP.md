# CineTaste v5 Cron Setup

## Overview

Runs the CineTaste pipeline (`./run`) automatically via cron.

## Files

| File | Purpose |
|------|---------|
| `install_cron.sh` | Installs/removes cron entries |
| `run_pipeline.sh` | Wrapper with locking, logging, env loading |
| `CRON_SETUP.md` | This documentation |

## Installation

```bash
# Production (runs daily at 8 PM)
./ops/scheduler/install_cron.sh production

# Dry-run mode
./ops/scheduler/install_cron.sh dry-run
```

## Configuration

Environment variables in `.env` or exported before install:

| Variable | Default | Description |
|----------|---------|-------------|
| `CINETASTE_CRON_INTERVAL` | `0 20 * * *` | Cron schedule (8 PM daily) |
| `CINETASTE_SCHEDULE_MODE` | `production` | `production` or `dry-run` |
| `CINETASTE_SCHEDULE_WHEN` | `now` | Date filter for movies |
| `CINETASTE_SCHEDULER_LOG` | `logs/scheduler.log` | Log file path |
| `CINETASTE_SCHEDULER_STATUS_LOG` | `logs/scheduler-status.log` | Status log path |
| `CINETASTE_SCHEDULER_MAX_ATTEMPTS` | `3` | Maximum whole-pipeline attempts for retryable failures |
| `CINETASTE_SCHEDULER_RETRY_DELAY_SECONDS` | `180` | Delay between retryable attempts |
| `CINETASTE_SCHEDULER_RETRY_EXIT_CODES` | `69` | Comma-separated pipeline exit codes that should be retried |

## Cron Entry Format

```
SHELL=/bin/bash
PATH=/home/pets/.local/bin:/home/pets/.npm-global/bin:/usr/local/bin:/usr/bin:/bin
MAILTO=""
0 20 * * * /home/pets/zoo/CineTaste_v5/ops/scheduler/run_pipeline.sh
```

## Features

1. **Locking**: Prevents overlapping runs via flock
2. **Logging**: All output to `logs/scheduler.log`
3. **Status tracking**: `logs/scheduler-status.log` for monitoring
4. **Env loading**: Auto-sources `.env` file
5. **Retry loop**: Retries source-unavailable pipeline failures before giving up
6. **Safe cleanup**: Removes old CineTaste entries before adding new

## Checking Status

```bash
# View scheduler logs
tail -f logs/scheduler.log

# View status history
cat logs/scheduler-status.log

# List current cron jobs
crontab -l
```
