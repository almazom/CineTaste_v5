# Review 4 — LLM/AgentOps Optic (Independent)

## 1) Executive Summary
CineTaste v5 has strong architectural discipline at the topology layer (contract-first, executable flow, manifested tools), but AgentOps governance is behind runtime reality.

The main gap is a **control-plane mismatch**:
- `PROTOCOL.json` + `FLOW.md` currently run `ct-cognize` with multi-agent fallback behavior.
- `AURA.md` and `.MEMORY/06-ai-agents.md` still center `ct-analyze` and an older `kimi → pi → dry_run` framing.

For an LLM-heavy stage at pipeline position 3 (`ct-cognize`), this mismatch creates operational risk: reviewers can follow stale policy while the system executes newer behavior. Missing pieces are: multi-agent review loops, explicit hallucination/over-polish controls, attention-budget rules, and severity policy for findings.

---

## 2) Missing Guidance for Multi-Agent Review Loops
Current docs define agent selection and preflight, but do not define **how outputs should be reviewed across agents**. In this repo architecture (`ct-fetch → ct-schedule → ct-cognize → ct-filter → ct-format → t2me`), missing guidance is:

1. **No two-pass review loop at stage 3 (`analysis-result`)**
- There is no required “producer agent + reviewer agent” loop before `ct-filter` consumes scores.
- Result: single-agent reasoning can pass schema validation but still carry semantic errors.

2. **No disagreement protocol between agents**
- Auto fallback handles failure, not quality disagreement.
- No policy for when primary/reviewer differ materially on `relevance_score` or `recommendation`.

3. **No contract-level review metadata**
- `analysis-result.meta` tracks `agent` and `web_search_used`, but not review lineage (`reviewed_by`, `review_status`, `delta_from_primary`).
- This limits observability in `logs/failed_*` and postmortems.

4. **No loop stopping conditions**
- Missing bounded loop rules (max passes, escalation threshold, abort semantics).
- Without bounds, review loops can drift into expensive or inconsistent behavior.

---

## 3) Missing Risk Controls (Hallucination, Over-Polishing, Attention Limits)

1. **Hallucination controls are implicit, not enforced**
- Prompt says “do not guess by title,” but no mandatory evidence field or source attribution rubric is enforced in contract.
- No automatic flag if agent reasoning references data absent from `movies.json`/`taste.yaml`.

2. **Over-polishing risk (false precision)**
- `confidence` is currently static (`0.8`) in `ct-cognize`, creating appearance of calibrated certainty without measurement.
- No rule to downgrade confidence when fallback agent is used after parse/runtime failures.

3. **Attention-budget controls are absent**
- No policy for large input batches (token budget, chunking, or prioritization before analysis).
- With long `movies.json`, model attention can degrade unevenly; late-list films may get shallow analysis.

4. **No safety gate before downstream amplification**
- `ct-filter` and `ct-format` amplify stage-3 decisions, but there is no quality gate for suspicious outputs (e.g., too many `must_see`, generic repeated reasoning).

---

## 4) Missing Prioritization Policy for Findings (P0..P4)
Current golden standard defines anti-patterns, but does not define severity triage. For this system, add:

1. **P0 — Send safety / architecture integrity breach**
- Examples: wrong contract shape crossing boundaries, corrupted `analysis-result`, or unsafe send behavior reaching `t2me`.
- Action: stop pipeline, block release, immediate fix.

2. **P1 — High-confidence semantic failure in stage 3**
- Examples: recommendation inversion for canon directors, systemic hallucinated attributes, major scoring collapse.
- Action: block production run; require re-analysis and reviewer signoff.

3. **P2 — Material quality degradation, recoverable**
- Examples: fallback-only runs with weak reasoning quality, large disagreement rates, repetitive reasoning text.
- Action: fix in next iteration; run targeted regression tests.

4. **P3 — Minor quality/documentation drift**
- Examples: stale agent docs (`ct-analyze` vs `ct-cognize`), incomplete metadata, missing examples.
- Action: schedule in documentation/ops sprint.

5. **P4 — Nice-to-have optimization**
- Examples: prompt style tuning, verbosity improvements, non-critical heuristics.
- Action: backlog.

---

## 5) Concrete Additions (Prompt Templates / Protocol Snippets)

### A. Add to `AURA.md` — Multi-Agent Review Loop Protocol
```md
## AgentOps Review Loop for ct-cognize (Stage 3)

After primary analysis (agent A), run reviewer pass (agent B) on the same inputs.

Required checks per movie:
- recommendation delta (A vs B)
- score delta (absolute)
- contradiction in key_matches/red_flags

Escalation rules:
- If recommendation differs by >= 2 tiers OR score delta > 25: mark REVIEW_REQUIRED
- If > 20% movies are REVIEW_REQUIRED: fail stage 3 with exit code 3

Loop bounds:
- Max 1 reviewer pass
- No recursive re-review
```

### B. Add to `PROTOCOL.json` — AgentOps policy block (topology-adjacent SSOT)
```json
"agentops": {
  "stage": "ct-cognize",
  "review_loop": {
    "enabled": true,
    "max_passes": 2,
    "reviewer_required": true,
    "max_score_delta": 25,
    "max_tier_delta": 1,
    "fail_if_review_required_ratio_gt": 0.20
  },
  "attention_policy": {
    "max_movies_per_pass": 20,
    "strategy": "chunk_then_merge"
  },
  "confidence_policy": {
    "static_confidence_forbidden": true,
    "must_include_basis": true
  }
}
```

### C. Prompt snippet for `ct-cognize` primary pass
```text
Output STRICT JSON only.
For each movie include:
- evidence: short list of exact fields used from movies.json/taste.yaml
- uncertainty: low|medium|high
Rule: If evidence is weak or missing, recommendation cannot exceed "maybe".
Rule: Never infer director/actors/genre not present in files unless explicitly marked "external_lookup".
```

### D. Prompt snippet for reviewer pass
```text
You are a strict reviewer of another agent's analysis.
Input files: movies.json, taste.yaml, primary_analysis.json.
Task:
1) Verify each movie recommendation against evidence.
2) Emit only disagreements with rationale.
3) Mark CRITICAL if canon/director rules were violated.
Output JSON: {"reviewed_by":"<agent>","review_required":[...],"summary":{...}}
```

### E. Add quality gate before `ct-filter`
```bash
# New stage: ct-guard (analysis quality gate)
# Input: analysis-result
# Output: analysis-result (validated/annotated) OR fail
```
Gate checks:
- repeated generic reasoning ratio
- recommendation distribution anomalies
- evidence-empty rows

---

## 6) Priority Matrix (High/Medium/Low)

| Gap | Priority | Why in This Repo |
|---|---|---|
| Align `AURA.md` + `.MEMORY/06-ai-agents.md` with `ct-cognize` reality | High | Current execution (`FLOW.md`/`PROTOCOL.json`) and operator guidance diverge |
| Define bounded multi-agent review loop for stage 3 | High | Stage 3 is the main semantic risk source before downstream send |
| Add hallucination evidence policy to output/prompt | High | Schema-valid outputs can still be factually wrong |
| Introduce confidence calibration policy (no static 0.8) | Medium | Reduces false certainty and improves operator trust |
| Add attention/chunking policy for large movie batches | Medium | Prevents context-window degradation and uneven quality |
| Add formal P0..P4 severity taxonomy to Golden Standard | Medium | Speeds triage and makes failures operationally consistent |
| Add optional style/verbosity improvements to reasoning text | Low | Cosmetic relative to pipeline safety and quality controls |

