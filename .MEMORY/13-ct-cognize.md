# `ct-cognize` — Cognitive Stage

> Purpose: analyze a `movie-schedule` payload against `taste/profile.yaml`
> Wrapper: `./ct-cognize`
> Contract: `movie-schedule@1.0.0 -> analysis-result@1.0.0`
> Updated: 2026-03-18

## What This Stage Does

`ct-cognize` owns stage 3 of the main pipeline.

Runtime sequence:

1. Validate `movie-schedule` input against the contract.
2. Select an agent chain from `tools/ct-cognize/agent-config.json`.
3. Write `movies.json` and `taste.yaml` into a temp workdir.
4. Run the agent prompt and parse the returned JSON array.
5. Merge AI judgments back into the original movie records.
6. Enforce `analysis-result@1.0.0`.

## Core CLI

```bash
./ct-cognize --input /tmp/scheduled.json --taste taste/profile.yaml
./ct-cognize --input /tmp/scheduled.json --taste taste/profile.yaml --agent pi
./ct-cognize --input /tmp/scheduled.json --taste taste/profile.yaml --agents qwen,pi,claude
./ct-cognize --input /tmp/scheduled.json --taste taste/profile.yaml --timings --verbose
cat /tmp/scheduled.json | ./ct-cognize --input - --taste taste/profile.yaml
```

## Current Agent Reality

Enabled today:

- `qwen`
- `pi`
- `claude`

Disabled in config:

- `kimi`
- `gemini`

Check current availability with:

```bash
./ct-cognize --list-agents
```

For preflight details, open [06-ai-agents.md](06-ai-agents.md).

## Prompt Rules That Matter

The current instruction inside `main.py` makes these rules explicit:

- be strict; most movies should become `skip`
- canonical directors from `taste.yaml canon` should become `must_see`
- favorite actors give a score bonus
- anime is treated as an automatic `must_see`
- the agent should inspect description, director, actors, and genres, not title only

If recommendation behavior changes unexpectedly, inspect the prompt in `tools/ct-cognize/main.py`.

## Output Notes

Each `analysis-result.analyzed[]` item contains:

- original `movie` payload
- `relevance_score`
- `recommendation`
- `reasoning`
- `key_matches`
- `red_flags`

The merge step preserves movie metadata from the input payload, so weak upstream metadata usually leads to weak reasoning.

## Failure Modes

| Symptom | Likely cause |
|--------|--------------|
| Contract error before preflight | invalid `movie-schedule` input |
| `No AI agent available` | all enabled agents failed preflight |
| Parse failure after agent run | agent returned non-JSON or malformed JSON |
| Weak reasoning | input payload lacked useful metadata |

## Practical One-Movie Workflow

```bash
# Build a one-movie schedule payload first
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/ --date 2026-03-29

# Then run cognition on the one-movie schedule
./ct-cognize --input /tmp/one-movie-scheduled.json --taste taste/profile.yaml --agent auto
```

## Related Cards

- [06-ai-agents.md](06-ai-agents.md)
- [10-ct-fetch.md](10-ct-fetch.md)
- [11-ct-schedule.md](11-ct-schedule.md)
- [12-ct-time-price.md](12-ct-time-price.md)

---
*Last updated: 2026-03-18*
