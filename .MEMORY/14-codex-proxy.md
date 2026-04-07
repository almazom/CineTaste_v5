# Proxy-Backed Codex — Headless Operator Flow

> Purpose: run headless Codex through the local round-robin proxy for manual review and debugging
> Wrapper: `codex_wp`
> Updated: 2026-04-07
> Source of Truth: `/home/pets/TOOLS/cdx_proxy_cli_v2/bin/codex_wp`, `cdx proxy --help`

This path is still primarily operator-facing, but `ct-cognize` may now use `codex_wp` as an optional fallback candidate when it is enabled in `tools/ct-cognize/agent-config.json`.

## Preferred Headless Path

Use `codex_wp` when you want the proxy bootstrap handled for you:

```bash
codex_wp exec -C /home/pets/zoo/CineTaste_v5 "inspect current changes"
codex_wp review -C /home/pets/zoo/CineTaste_v5 --uncommitted
cat /tmp/review-prompt.md | codex_wp review -C /home/pets/zoo/CineTaste_v5 --uncommitted
```

What `codex_wp` does:

- starts or reuses the local proxy with `cdx proxy --print-env-only`
- reads `CLIPROXY_BASE_URL`
- runs `codex` with `-c "openai_base_url=..."`
- unsets conflicting `OPENAI_BASE_URL` / `OPENAI_API_BASE`
- adds `--dangerously-bypass-approvals-and-sandbox`

## Manual Path When You Need Custom Flags

Use the manual proxy export when you want to control sandbox or approval flags yourself:

```bash
eval "$(cdx proxy --print-env-only)"
codex -C /home/pets/zoo/CineTaste_v5 review --uncommitted
codex -C /home/pets/zoo/CineTaste_v5 exec --sandbox workspace-write -a never "inspect current changes"
```

Rule:

- prefer `codex_wp` for quick headless runs
- prefer manual `eval "$(cdx proxy --print-env-only)"` when you do not want the wrapper's forced danger mode

## Zellij Pane Discipline

When running review panes manually:

- reuse the existing review tab instead of creating extra tabs mid-run
- launch one pane first and confirm it is alive before launching the next pane
- after sending a command, inspect pane scrollback and output files periodically
- if a pane errors immediately, stop and fix that path before touching the other panes

Example single-pane review:

```bash
pwd
cat /tmp/review-prompt.md | codex_wp review --uncommitted |& tee /tmp/review-output.md
```

## Monitoring

Check proxy health while the run is active:

```bash
cdx status --json
cdx doctor
cdx trace
```

Useful runtime checks:

```bash
pgrep -af 'openai_base_url='
tail -n 50 ~/.codex/_auths/rr_proxy_v2.log
```

Healthy proxy signals:

- `cdx status --json` shows `healthy: true`
- `base_url` is a live local loopback URL such as `http://127.0.0.1:45539`
- at least one auth profile remains `OK` in `cdx doctor`

## Common Failure Modes

| Symptom | Likely cause | First check |
|--------|--------------|-------------|
| Direct Codex says usage limit reached | You bypassed proxy or hit one account directly | use `codex_wp` or confirm `openai_base_url` points at the proxy |
| Proxy-backed run stalls before model output | proxy unhealthy or auth pool exhausted | `cdx status --json`, `cdx doctor` |
| Many accounts are blacklisted | upstream auth rotation is degraded | `cdx doctor`, `cdx trace` |
| Wrong sandbox/approval behavior | `codex_wp` forced danger mode | use manual proxy env plus direct `codex` flags |

## Related Cards

- [06-ai-agents.md](06-ai-agents.md)
- [13-ct-cognize.md](13-ct-cognize.md)
