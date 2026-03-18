# `ct-schedule` — Collect Showtimes

> Purpose: enrich a `movie-batch` payload with showtimes
> Wrapper: `./ct-schedule`
> Contract: `movie-batch@1.0.0 -> movie-schedule@1.0.0`
> Updated: 2026-03-18

## What This Stage Owns

`ct-schedule` is the stage-2 collector between fetch and cognition.

It:
- loads a validated `movie-batch`
- resolves showtimes per movie URL
- attaches `showtimes[]` to each movie
- emits the canonical `movie-schedule` payload for `ct-cognize`

## Core CLI

```bash
./ct-schedule --input /tmp/movies.json --output /tmp/scheduled.json
./ct-schedule --input /tmp/movies.json --date 2026-03-29 --output /tmp/scheduled.json
./ct-schedule --input /tmp/movies.json --best-effort --output /tmp/scheduled.json
./ct-schedule --input /tmp/movies.json --dry-run
```

## Date Behavior

- If `--date` is passed, it wins.
- Otherwise `ct-schedule` uses `input.meta.date`.
- If `input.meta.date` is missing or empty, it falls back to local today.

For presale / advance-sale titles, pass the exact page date instead of assuming the batch date is correct.

## Failure Policy

Default behavior is fail-fast:

- if showtime fetches fail for one or more movies, the tool exits with upstream error `69`

Use `--best-effort` when you want a partial `movie-schedule` anyway:

- failed movies get empty `showtimes`
- successful movies continue through the stage

## Output Notes

Important metadata in `movie-schedule.meta`:

- `date`: schedule date actually used
- `scheduled_at`: enrichment timestamp
- `schedule_source`: usually `kinoteatr.ru`
- `movies_total`: all input movies
- `movies_with_showtimes`: only the movies that resolved at least one session

## Practical Workflow

1. Run `ct-fetch`.
2. Filter to the movie subset you care about if needed.
3. Run `ct-schedule`.
4. Pass the result to `ct-cognize`.

## Common Gotchas

- Movies without `url` get empty `showtimes`.
- `ct-time-price` output is not a drop-in replacement for `movie-schedule`; it must be merged or wrapped if you want to run `ct-cognize` on one title.
- Batch date and real page date can diverge for presales.

## Related Cards

- [10-ct-fetch.md](10-ct-fetch.md)
- [12-ct-time-price.md](12-ct-time-price.md)
- [13-ct-cognize.md](13-ct-cognize.md)

---
*Last updated: 2026-03-18*
