# Taste Profile — CineTaste v5

## What It Is

`taste/profile.yaml` defines user preferences used by `ct-cognize` to score movies.

## Core Structure

```yaml
version: "1.0"
user: "default"

likes:
  directors: []
  genres: []
  keywords: []

dislikes:
  directors: []
  genres: []
  keywords: []

canon:
  - director: "Name"
    weight: 1.0

thresholds:
  must_see: 85
  recommended: 60
  maybe: 40
```

## Runtime Use

1. `ct-cognize` loads validated `movie-schedule` input.
2. Agent reads `movies.json` and `taste.yaml` from working directory.
3. Agent returns per-movie recommendation JSON.
4. Output is enforced against `analysis-result` contract.

## Recommendation Buckets

| Category | Typical Score Band |
|----------|--------------------|
| `must_see` | 85-100 |
| `recommended` | 60-84 |
| `maybe` | 40-59 |
| `skip` | 0-39 |

## Editing Workflow

```bash
# Edit profile
nano taste/profile.yaml

# Validate pipeline with cached analysis replay
./run --input contracts/examples/analysis-result.sample.json
```

## Practical Guidance

1. Prefer specific directors/actors over broad labels.
2. Keep dislikes explicit to reduce false positives.
3. Revisit thresholds only after reviewing several daily runs.
4. Track recommendation drift via pipeline logs.

---
*Last updated: 2026-03-05*
