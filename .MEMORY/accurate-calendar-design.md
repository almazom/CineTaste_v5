# Design: Accurate Movie Calendar Using data-dates

## Problem
- Listing page `/kinoafisha/` shows movies with showtimes for a specific day
- But `data-dates` on detail pages reveals the TRUE schedule
- Example: "Андрей Рублев" shows 18:00 today, but `data-dates="2026-03-21"` suggests it actually plays March 21
- We're missing movies scheduled beyond our 7-day fetch window

## Solution: Two-Phase Fetch

### Phase 1: Discovery (Quick)
Fetch listing page to get all movie URLs (current behavior)

### Phase 2: Enrichment (Accurate)
For each movie, fetch detail page and extract `data-dates` attribute
This gives us the REAL available days

## Implementation Options

### Option A: Extend ct-fetch (Recommended)
Add `--accurate` flag that:
1. Gets movie list from listing page
2. Fetches each movie's detail page
3. Extracts `data-dates` from HTML
4. Uses THAT as available_days (not aggregated listing pages)

Pros:
- Accurate scheduling
- Catches movies scheduled >7 days out
- Single tool, clean interface

Cons:
- Slower (N movies = N+1 HTTP requests)
- More load on kinoteatr.ru

### Option B: New ct-calendar Tool
Create separate tool that:
- Takes movie-batch as input
- Fetches all detail pages
- Outputs movie-batch with accurate available_days

Pros:
- Modular, reusable
- Can run independently

Cons:
- Another pipeline stage
- More complexity

### Option C: Extend ct-schedule
Use existing detail page fetching in ct-schedule
Extract `data-dates` while fetching showtimes

Pros:
- Reuses existing HTTP calls
- No extra requests

Cons:
- ct-schedule purpose is showtimes, not discovery
- Mixes concerns

## Recommendation: Option A — Extend ct-fetch

Add to ct-fetch:
```bash
ct-fetch --city naberezhnie-chelni --when accurate  # Uses data-dates from detail pages
ct-fetch --city naberezhnie-chelni --when week      # Current behavior (listing pages)
```

### Changes needed:
1. adapter_kinoteatr.py: Add `fetch_movies_accurate()`
2. Extract `data-dates` regex: `data-dates="([^"]+)"`
3. Parse comma-separated dates
4. Use THAT as available_days

### CLI for ./run:
```bash
./run --accurate    # Use data-dates for accurate scheduling
./run --week        # Current 7-day listing fetch
./run               # Today's listing only
```

## Benefits
- Accurate movie scheduling
- Discover movies playing >7 days out
- Don't miss films like "Андрей Рублев" on March 21
