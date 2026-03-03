# Gemini Agent Guide — CineTaste v5

## Use `@aura.md` First

`@aura.md` means the repository root `AURA.md` (symlink to `.aura/latest/AURA.md`).

1. Bootstrap every session in this order: `@aura.md` → `PROTOCOL.json` → `.MEMORY/00-index.md` → `flows/latest/FLOW.md`.
2. Before implementation, create a timestamped kanban in `.aura/kanban/`, point `.aura/kanban/latest` to it, and track only `TODO/DOING/DONE`.
3. Treat `PROTOCOL.json` as topology SSOT and `@aura.md` as execution protocol.
4. Apply AURA workflow exactly: `CONTRACT → KANBAN → TOOL → FLOW → TEST → VERSION`.
