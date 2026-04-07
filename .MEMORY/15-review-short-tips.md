# Review Short Tips

Use this card when:

- you need a fast mental model of CineTaste v5
- you want to extend the pipeline without violating the SSOT runtime rules
- you need to remember what changed from older CineTaste versions

Core idea:

- this repo is the contract-first, protocol-driven evolution of CineTaste
- it turns cinema listings into Telegram recommendations through CLI microservices
- v5’s key change is the stricter runtime discipline around `PROTOCOL.json` + `flows/latest/FLOW.md`
- the cognitive stage is now `ct-cognize`; older `ct-analyze` is legacy thinking

Active pipeline:

`ct-fetch -> ct-schedule -> ct-cognize -> ct-filter -> ct-format -> t2me`

What matters most:

- `PROTOCOL.json` is the system SSOT
- `./run` reads `PROTOCOL.json` and `flows/latest/FLOW.md` on every execution
- contracts define boundaries between microservices
- `ct-cognize` is the product intelligence core
- safe dry-run still exercises all stages and validates Telegram send with `t2me --dry-run`

Fast read order:

1. `README.md`
2. `AURA.md`
3. `PROTOCOL.json`
4. `.MEMORY/00-index.md`
5. `flows/latest/FLOW.md`
6. `.MEMORY/06-ai-agents.md`
7. `.MEMORY/13-ct-cognize.md`

High-value commands:

```bash
./run
./run --dry-run
./run --input contracts/examples/analysis-result.sample.json
./run --resend message.txt
make test
make test-cov
```

Operational truths:

- the repo is microservice-shaped: each tool should stay narrow
- contract enforcement is part of normal execution, not just tests
- agent selection for `ct-cognize` is explicit and can involve preflight race/fallback
- Telegram delivery is a first-class final surface
- older architecture ideas from v3/v4 are useful context but should not override v5 SSOT files

Current strengths:

- clearer SSOT discipline than earlier CineTaste versions
- good microservice split
- explicit cognitive-stage handling
- practical dry-run and replay modes

Current review cautions:

- do not bypass `PROTOCOL.json` and flow files with hidden runtime shortcuts
- if changing `ct-cognize`, also review agent-preflight and proxy assumptions
- if changing stage order, update the flow/SSOT before implementation
- keep legacy stage names from confusing the active runtime story

Short reviewer verdict:

- think of v5 as the mature protocol-driven CineTaste runtime
- preserve SSOT execution, contract clarity, and the cognitive stage as the main product differentiator
- if changing behavior, change the declared protocol first, then the code
