# `ct-fetch` — Batch Discovery

> Purpose: fetch a city movie list from kinoteatr.ru
> Wrapper: `./ct-fetch`
> Contract: `— -> movie-batch@1.0.0`
> Updated: 2026-03-18

## When To Use It

Use `ct-fetch` when you need the canonical batch list for a city:

- today's movies
- a specific date
- a 7-day aggregated batch
- a starting point for `ct-schedule`

## Core CLI

```bash
./ct-fetch --city naberezhnie-chelni
./ct-fetch --city naberezhnie-chelni --when week --output /tmp/movies.json
./ct-fetch --city naberezhnie-chelni --when 2026-03-29 --output /tmp/movies.json
./ct-fetch --city naberezhnie-chelni --dry-run
```

## Flag Semantics

| Flag | Meaning |
|------|---------|
| `--city` | Required city code such as `naberezhnie-chelni` |
| `--when now` | Fetch today's visible listing |
| `--when week` | Aggregate 7 days into one `movie-batch` |
| `--when YYYY-MM-DD` | Fetch a concrete date |
| `--output` | Write JSON to a file instead of stdout |
| `--dry-run` | Emit deterministic test data |
| `--verbose` | Print fetch diagnostics to stderr |

## Output Notes

Important fields in `movie-batch`:

- `movies[]`: raw movie records
- `meta.date`: today for `now`, explicit date for `YYYY-MM-DD`, current date for `week`
- `meta.mode=week` and `meta.days_fetched=7` only in week mode
- `available_days`: aggregated play dates discovered during week fetch
- `available_days_accurate`: detail-page `data-dates` values and the better source of truth when they disagree

## Practical Workflow

1. Use `--when now` to answer "what is playing today?"
2. Use `--when week` when a title might be a presale or missing from today's list.
3. Filter the resulting JSON down to one movie before passing it to `ct-schedule` or combining it with `ct-time-price`.

## Common Gotchas

- Week output can include movies that are not actually playing today.
- `raw_description` may be sparse; fetch is a discovery stage, not a deep metadata stage.
- If a title exists only as an advance sale, the week batch may surface it while `available_days_accurate` points to a later exact date.

## Related Cards

- [11-ct-schedule.md](11-ct-schedule.md)
- [12-ct-time-price.md](12-ct-time-price.md)
- [13-ct-cognize.md](13-ct-cognize.md)

---
*Last updated: 2026-03-18*
