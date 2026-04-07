# `ct-fetch` — Batch Discovery

> Purpose: fetch a city movie list from kinoteatr.ru
> Wrapper: `./ct-fetch`
> Contract: `— -> movie-batch@1.0.0`
> Updated: 2026-04-07

## When To Use It

Use `ct-fetch` when you need the canonical batch list for a city:

- today's movies
- a specific date
- a 7-day aggregated batch
- a 30-day aggregated batch
- a starting point for `ct-schedule`

## Core CLI

```bash
./ct-fetch --city naberezhnie-chelni
./ct-fetch --city naberezhnie-chelni --when week --output /tmp/movies.json
./ct-fetch --city naberezhnie-chelni --when month --output /tmp/movies.json
./ct-fetch --city naberezhnie-chelni --when 2026-03-29 --output /tmp/movies.json
./ct-fetch --city naberezhnie-chelni --dry-run
```

## Flag Semantics

| Flag | Meaning |
|------|---------|
| `--city` | Required city code such as `naberezhnie-chelni` |
| `--when now` | Fetch today's visible listing |
| `--when week` | Aggregate 7 days into one `movie-batch` |
| `--when month` | Aggregate 30 days into one `movie-batch` |
| `--when YYYY-MM-DD` | Fetch a concrete date |
| `--output` | Write JSON to a file instead of stdout |
| `--dry-run` | Emit deterministic test data |
| `--verbose` | Print fetch diagnostics to stderr |

## Output Notes

Important fields in `movie-batch`:

- `movies[]`: raw movie records
- `meta.date`: today for `now`, explicit date for `YYYY-MM-DD`, current date for aggregated horizons
- `meta.mode=week|month` and `meta.days_fetched` for aggregated horizons
- `available_days`: aggregated play dates discovered during week/month fetch
- `available_days_accurate`: detail-page `data-dates` values and the better source of truth when they disagree

## Reliability Notes

- The adapter normalizes the env-provided listing URL before adding the `when` query, so stale `?when=...` fragments in `.env` do not corrupt later requests.
- Transient upstream responses such as `502`, `503`, `504`, `429`, and network timeouts are retried with short backoff before the command exits with source-unavailable status.
- If `ddos-guard` is returning a stable `502` for both listing and detail pages, that is an upstream outage and not something `ct-fetch` can fully solve on its own.
- `./run` may still continue in degraded mode after a `ct-fetch` exit `69` by reusing the newest cached `artifacts/movies.json` for the same city and forcing `ct-schedule --best-effort`; disable that with `CT_FETCH_CACHE_FALLBACK=0` if you need strict failure semantics.

## Practical Workflow

1. Use `--when now` to answer "what is playing today?"
2. Use `--when week` when a title might surface within the next 7 days.
3. Use `--when month` when presales or later taste matches may land within the next 30 days.
4. Filter the resulting JSON down to one movie before passing it to `ct-schedule` or combining it with `ct-time-price`.

## Common Gotchas

- Aggregated output can include movies that are not actually playing today.
- `raw_description` may be sparse; fetch is a discovery stage, not a deep metadata stage.
- If a title exists only as an advance sale, the week/month batch may surface it while `available_days_accurate` points to a later exact date.

## Related Cards

- [11-ct-schedule.md](11-ct-schedule.md)
- [12-ct-time-price.md](12-ct-time-price.md)
- [13-ct-cognize.md](13-ct-cognize.md)

---
*Last updated: 2026-04-07*
