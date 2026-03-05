# Documentation UX / Readability / Typography Review

## 1) Executive Summary

The documentation has strong architectural intent and a polished visual baseline, but UX trust is weakened by narrative drift and entry-point friction.

- The most critical gap is **cross-doc inconsistency**: `README.md` still describes `v5.3.0` and `ct-analyze`, while active protocol/flow has moved to `v5.4.0` and `ct-cognize`.
- The second major gap is **theory-first presentation**. Current docs explain principles well, but they are not optimized for fast task execution by different audiences.
- The HTML edition is visually premium, but **reading ergonomics can improve** (text measure, heading treatment, navigational scaffolding).

Net: quality is high in tone and structure, but practical readability and operational clarity are currently below “gold standard” due to stale and non-task-oriented information architecture.

## 2) Clarity/readability gaps for different audiences

| Audience | What they need in first 60-120 seconds | Current gap | Impact | Improvement |
|---|---|---|---|---|
| New contributor | “How do I run this safely right now?” | README opens with release notes and legacy pipeline wording, not a role-based quick path | Slow onboarding, wrong mental model | Add `Start Here` with 3 paths: run, modify contract, debug |
| Returning maintainer | “What changed since last version?” | README says `v5.3.0` while protocol/flow are `v5.4.0`; pipeline diagram still names `ct-analyze` | Trust erosion, accidental wrong tool usage | Add SSOT-synced version block and single-source pipeline snippet |
| AI agent/operator | “What is mandatory vs optional?” | Rules are spread across AURA/README/Golden Standard; some statements are duplicated without priority markers | Execution ambiguity, policy drift | Add explicit “Priority of truth” callout in README and golden-standard |
| Reviewer/architect | “Is this document doctrine, runbook, or changelog?” | Golden Standard blends mission, policy, and operational checks without a short decision map | High cognitive load, hard to audit quickly | Add one-page “Document map” and “When to read what” table |

Additional readability notes:

- Golden Standard prose is clear but dense; paragraph lengths and repeated rhetorical framing reduce skim speed.
- Lists are abundant but not grouped by actionability (`must`, `should`, `example`), making urgency less visible.
- README command blocks are useful, but expected outcomes are missing (what success/failure looks like).

## 3) Information architecture gaps

1. **Canonical entry path is not explicit enough in user-facing docs.**  
   Bootstrap order exists in AURA/Memory, but README does not strongly route users through the same path.

2. **Version and topology messaging are fragmented.**  
   README, Golden Standard, and live protocol/flow are not aligned around one “current state” panel.

3. **Purpose vs execution are mixed.**  
   Golden Standard mixes doctrine and operational checks in one linear stream; users need split lanes:
   - Strategic doctrine (why)
   - Operational protocol (how)
   - Task runbook (do this now)

4. **No “decision-by-task” navigation.**  
   Missing compact IA for common intents:
   - “I need to run pipeline”
   - “I need to add tool”
   - “I need to modify contract”
   - “I need to recover from failure”

5. **Cross-linking is underleveraged.**  
   Docs reference files, but do not create a guided progression with “next document” links.

## 4) HTML typography/layout gaps and improvements

Strengths:

- Palette and serif/sans pairing create an editorial feel.
- Contrast is generally safe for body and muted text.
- Spacing and card presentation are coherent and premium.

Gaps and concrete improvements:

1. **Reading measure is too wide for long-form policy text.**  
   `.sheet { max-width: 960px; }` can produce long lines for prose.  
   Improve with a text measure wrapper near `68-74ch` for paragraphs/lists.

2. **All-caps `h2` reduces scan efficiency on dense documentation.**  
   Current uppercase + letter spacing looks elegant but slows semantic parsing.  
   Use sentence/title case for section headers; reserve uppercase for small metadata labels.

3. **Navigation scaffolding is missing.**  
   Add a top Table of Contents with anchor links for quick jumps between principles and compliance sections.

4. **No dedicated styling for future block code samples.**  
   Inline `code` is styled; `pre code` is not. Add block code styles before docs expand.

5. **No print mode for policy artifact usage.**  
   Add `@media print` to remove background gradients/shadows and optimize for clean archival print/PDF.

6. **Long sections need progressive structure aids.**  
   Add “Key takeaways” callouts per major section to support skim readers before full prose.

## 5) Concrete content and layout additions

### A. README content additions

1. Add `Start Here (90 seconds)` with:
   - `Run pipeline now`
   - `Change contract safely`
   - `Debug failed run`
2. Add `Current Runtime Snapshot` generated from SSOT (version, active flow, active stage chain).
3. Add `Expected Output` under each quick command (example success artifact paths/log lines).
4. Add `Last verified against PROTOCOL.json: YYYY-MM-DD` line to enforce editorial freshness.

### B. Golden Standard markdown additions

1. Add `TL;DR` section at top with 5 non-negotiables.
2. Add `Who this is for` audience map.
3. Add `Decision Table: Which file do I edit?` (`PROFILE`, `AURA`, `PROTOCOL`, `FLOW`, `MANIFEST`, contracts).
4. Add `Compliant change mini-template` (checkpoints + evidence links).
5. Add `Glossary` for project terms (`SSOT`, `contract-first`, `replaceability`, `executable markdown`).

### C. Golden Standard HTML layout additions

1. Add sticky in-page ToC on desktop, collapsible ToC on mobile.
2. Apply `max-width` by character measure to long text blocks.
3. Convert major section breaks into clearer visual rhythm:
   - lighter top rules,
   - more whitespace before section titles,
   - short section intro text style.
4. Add print stylesheet and visible “Last updated” metadata area.
5. Add semantic landmarks: `main`, `nav`, and section IDs for deep-linking.

## 6) Priority matrix (High/Medium/Low)

| Priority | Item | Why now | Effort |
|---|---|---|---|
| High | Align README with active topology (`v5.4.0`, `ct-cognize`, current flow) | Removes immediate trust and onboarding errors | S |
| High | Add task-first entry section in README | Fastest usability gain for all audiences | S |
| High | Add canonical “current runtime snapshot” sourced from SSOT | Prevents future doc drift | M |
| Medium | Add doc-map/decision-table to Golden Standard | Reduces cognitive load for maintainers and reviewers | S |
| Medium | Introduce ToC + anchor navigation in HTML version | Improves scanning and non-linear reading | M |
| Medium | Improve typography measure and heading treatment in HTML | Better long-form readability without redesign | S |
| Low | Add print styles and archival metadata block in HTML | Useful for governance workflows, less urgent | S |
| Low | Add glossary and example-driven policy snippets | Increases editorial clarity over time | M |

---

Editorial verdict: the project already has strong doctrine and visual identity; the next quality leap is **synchronization + task-oriented readability**.
