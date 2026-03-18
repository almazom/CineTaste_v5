# `ct-time-price` — Single Movie URL Probe

> Purpose: fetch showtimes and price labels for one selected movie page
> Wrapper: `./ct-time-price`
> Contract: `— -> movie-showtimes@1.0.0`
> Updated: 2026-03-18

## What It Is For

`ct-time-price` is the smallest useful inspection tool when you already have one movie URL.

Use it for:

- checking whether a movie page has sessions
- confirming the exact date shown on a page
- getting `time`, `price`, `hall`, and booking URL for one title
- debugging batch-vs-page mismatches before constructing a one-movie `movie-schedule`

It is not part of the main `./run` pipeline.

## Core CLI

```bash
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/ --date 2026-03-29
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/ --output /tmp/showtimes.json
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/ --dry-run
```

## Date Behavior

- Default `--date` is local today.
- That default is fine for "what is playing now?" checks.
- For presale / `предпоказ` pages, pass the explicit page date. Otherwise the output may reflect a local date wrapper around sessions that actually belong to a later scheduled day.

## Output Shape

The `movie-showtimes` contract gives you:

- `movie_url`
- `date`
- `showtimes[]`
- `meta.source`
- `meta.showtimes_count`

What it does not give you:

- title
- genres
- description
- taste relevance

If you want cognition, you still need a valid `movie-schedule` payload.

## Practical Workflow

1. Use `ct-fetch --when week` to confirm the movie exists in batch context.
2. Use `ct-time-price` to verify the exact page date/time/price.
3. Merge that result into a one-movie `movie-schedule`.
4. Run `ct-cognize`.

## Adapter Notes

`ct-time-price` reuses the same Kinoteatr showtime adapter as `ct-schedule`.

That means:

- the parsing behavior should stay aligned across single-movie and batch scheduling
- fixes in the shared adapter affect both tools

## Related Cards

- [10-ct-fetch.md](10-ct-fetch.md)
- [11-ct-schedule.md](11-ct-schedule.md)
- [13-ct-cognize.md](13-ct-cognize.md)

---
*Last updated: 2026-03-18*
