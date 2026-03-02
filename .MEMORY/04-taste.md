# 🎬 Taste Profile — CineTaste v5

## What is the Taste Profile?

A YAML file that defines user preferences for movie recommendations.

**Location:** `taste/profile.yaml`

## Structure

```yaml
version: "1.0"
user: "default"

likes:
  directors:
    - "Tarkovsky"
    - "Lynch"
    - "A24"
  genres:
    - "art-house"
    - "anime"
    - "indie"
  keywords:
    - "philosophical"
    - "surreal"

dislikes:
  directors: []
  genres:
    - "horror"
    - "blockbuster"
  keywords:
    - "mainstream"

canon:
  - director: "Tarkovsky"
    weight: 1.0
  - director: "Kubrick"
    weight: 0.9

thresholds:
  must_see: 85
  recommended: 60
  maybe: 40
```

## How It Works

1. **ct-analyze** reads `taste/profile.yaml`
2. AI compares each movie against likes/dislikes
3. Score calculated based on matches and weights
4. Recommendation assigned: `must_see`, `recommended`, `maybe`, `skip`

## Recommendation Categories

| Category | Score Range | Action |
|----------|-------------|--------|
| `must_see` | 85-100 | Always include |
| `recommended` | 60-84 | Include if space |
| `maybe` | 40-59 | Optional |
| `skip` | 0-39 | Exclude |

## Modifying Taste

```bash
# Edit the profile
nano taste/profile.yaml

# Test changes
./run --dry-run

# Verify output
cat /tmp/ct-format/message.txt
```

## Best Practices

1. **Be specific** — Named directors > generic genres
2. **Use weights** — Some preferences are stronger
3. **Review periodically** — Taste evolves
4. **Test before production** — Always use --dry-run first

---
*Last updated: 2026-03-02*
