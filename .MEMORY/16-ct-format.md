# `ct-format` — Telegram Rendering

> Purpose: render `filter-result` into Telegram-ready markdown text
> Wrapper: `./ct-format`
> Contract: `filter-result@1.0.0 -> message-text@1.0.0`
> Updated: 2026-04-07

## What This Stage Does

`ct-format` turns filtered movie matches into the final Telegram message.

Current layout is horizon-based:

- `СЕГОДНЯ`
- `В БЛИЖАЙШИЕ 7 ДНЕЙ`
- `В БЛИЖАЙШИЕ 30 ДНЕЙ`

## Bucket Rules

- Today bucket uses play dates where `day_delta == 0`
- Week bucket uses `1..7` days ahead
- Month bucket uses `8..30` days ahead
- If a movie has dates in several horizons, the earliest matching horizon wins
- If no date metadata exists, the renderer falls back to the today bucket for backward compatibility

## Date Sources

The renderer prefers these fields in this order:

1. `movie.available_days_accurate`
2. `movie.available_days`
3. `movie.showtimes[].datetime_iso`

This matters for presales and long-horizon fetches: `available_days_accurate` from the detail page is the best source of truth.

## Empty-State Policy

All three sections stay visible even when a bucket is empty.

Current empty copy:

- `Сегодня ничего не подходит`
- `В ближайшие 7 дней ничего не подходит`
- `В ближайшие 30 дней ничего не подходит`

This keeps the month-aware pipeline readable in Telegram even on sparse days.

## Link Policy

- A movie title is rendered as a markdown link only when `movie.url` is present
- If no `url` exists, the title stays plain text
- Linkability usually depends on `ct-fetch` successfully joining the card title with the kinoteatr anchor URL

## Relative-Date Copy

Future buckets show both the exact date and a human-readable distance from today.

Examples:

- `📆 25.04`
- `⏳ через 18 дней`

Current wording rules:

- `завтра`
- `послезавтра`
- `через неделю`
- `через 2 недели`, `через 3 недели`, `через 4 недели`
- otherwise `через N дней`

## Practical Checks

```bash
./ct-format --input /tmp/filtered.json --template telegram --city "Набережные Челны" --output /tmp/message.json
python3 -m pytest tests/test_ct_format.py -q
```

## Related Cards

- [10-ct-fetch.md](10-ct-fetch.md)
- [11-ct-schedule.md](11-ct-schedule.md)
- [13-ct-cognize.md](13-ct-cognize.md)

---
*Last updated: 2026-04-07*
