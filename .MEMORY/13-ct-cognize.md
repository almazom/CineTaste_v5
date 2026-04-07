# `ct-cognize` — Cognitive Stage

> Purpose: analyze a `movie-schedule` payload against `taste/profile.yaml`
> Wrapper: `./ct-cognize`
> Contract: `movie-schedule@1.0.0 -> analysis-result@1.0.0`
> Updated: 2026-04-07

## What This Stage Does

`ct-cognize` owns stage 3 of the main pipeline.

Runtime sequence:

1. Validate `movie-schedule` input against the contract.
2. Load and normalize `taste/profile.yaml`.
3. Compute deterministic rule signals for each movie.
4. Select an agent chain from `tools/ct-cognize/agent-config.json`.
5. Write `movies.json`, `taste.yaml`, and `rule_signals.json` into a temp workdir.
6. Run the agent prompt and parse the returned JSON array.
7. Merge AI judgments back through the rules-first bounds and confidence gates.
8. Enforce `analysis-result@1.0.0`.

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
- `rule_signals.json` defines deterministic `rule_score`, floor, ceiling, and metadata confidence
- anime and canon matches are stabilized before the agent refines anything
- if the user likes anime and a page is missing genre tags, known anime-creator directors can still force a `recommended` floor
- sparse metadata should lower confidence and prevent unjustified `must_see`
- the agent still inspects description, director, actors, and genres, but only as bounded refinement over the rule layer

If recommendation behavior changes unexpectedly, inspect the prompt in `tools/ct-cognize/main.py`.

## Output Notes

Each `analysis-result.analyzed[]` item contains:

- original `movie` payload
- `relevance_score`
- `rule_score`
- `llm_delta`
- `recommendation`
- `confidence`
- `review_required`
- `reasoning`
- `decision_basis`
- `key_matches`
- `red_flags`

The merge step preserves movie metadata from the input payload and now adds a deterministic quality trace, so strong anime/canon matches should stop drifting between runs.

Current practical effect:

- explicit `аниме` genres still force `must_see`
- known anime creators on sparse pages can keep a film in `recommended`
- `review_required=true` still marks low-confidence recommendations so the shortlist can stay visible without pretending certainty

## Failure Modes

| Symptom | Likely cause |
|--------|--------------|
| Contract error before preflight | invalid `movie-schedule` input |
| `No AI agent available` | all enabled agents failed preflight |
| Parse failure after agent run | agent returned non-JSON or malformed JSON |
| Weak reasoning | input payload lacked useful metadata or the agent ignored `rule_signals.json` |
| High score but `review_required=true` | rule layer detected low confidence or strong rule/LLM tension |

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
