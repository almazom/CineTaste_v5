# Coming Week Feature Design

## Problem
Movies that fit the user's taste profile may not be playing TODAY, but might play TOMORROW or later this week. Currently, the pipeline only fetches movies for a single day (`--when now` or specific date).

## Solution
Add a `--week` mode that:
1. Fetches movies for the next 7 days
2. Aggregates unique movies across all days
3. Identifies which days each movie plays
4. Shows "Today's Picks" + "Coming This Week" sections

## Architecture

### Option A: Extend ct-fetch (Recommended)
Add `--when week` to ct-fetch that outputs aggregated week data:

```json
{
  "movies": [...],
  "meta": {
    "mode": "week",
    "date_range": ["2026-03-10", "2026-03-16"],
    "movies_total": 25,
    "movies_unique": 18
  }
}
```

Each movie includes `showtimes_by_day`:
```json
{
  "id": "kt-sekretnyy-agent",
  "title": "Секретный агент",
  "showtimes_by_day": {
    "2026-03-11": [{"time": "19:00", "hall": "Стандарт"}],
    "2026-03-13": [{"time": "18:30", "hall": "Screen Max"}]
  }
}
```

### Option B: New ct-week tool (Alternative)
Create separate tool that aggregates multiple fetch calls. More complex, adds another stage.

## Recommended: Option A - Extend Existing Tools

### Changes Needed

#### 1. ct-fetch: Add `--when week` support
- Loop through next 7 days
- Fetch each day
- Deduplicate by movie ID
- Aggregate showtimes by day

#### 2. ct-schedule: Handle week mode
- Process showtimes_by_day for each movie
- Output same format (movie-schedule contract remains compatible)

#### 3. ct-format: Add "Coming Week" section
- Split movies into:
  - `playing_today`: Movies with showtimes today
  - `coming_later`: Movies with showtimes only on future days
- Render two sections in Telegram message

### Example Output

```
🎬 Кино на сегодня (10 марта)

🌟 Рекомендовано

[Today's movies that match taste]

─────────────────────────────
📅 На этой неделе

🎞 Секретный агент
   Режиссёр: Клебер Мендонса Фильо
   Совпадение: 88% — must see
   📆 Будет: 11 марта (вт) в 19:00, 13 марта (чт) в 18:30

🎞 Убийство священного оленя
   Режиссёр: Йоргос Лантимос
   Совпадение: 92% — must see
   📆 Будет: 12 марта (ср) в 20:00
```

## Implementation Plan

1. **Phase 1**: Extend ct-fetch with `--when week`
2. **Phase 2**: Update ct-format to render two sections
3. **Phase 3**: Add `--week` flag to ./run script
4. **Phase 4**: Test with real data

## Benefits
- User doesn't miss movies that fit their taste just because they're not playing today
- Can plan cinema visits in advance
- Simple UX: just run `./run --week` instead of `./run --when 2026-03-11`
