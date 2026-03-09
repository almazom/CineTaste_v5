"""Doc and memory sync checks for active runtime semantics."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_memory_architecture_mentions_dry_run_mode():
    architecture = (ROOT / ".MEMORY" / "01-architecture.md").read_text(encoding="utf-8")
    protocol = json.loads((ROOT / "PROTOCOL.json").read_text(encoding="utf-8"))
    assert "--dry-run" in architecture
    assert "dry_run" in protocol["flow"]["modes"]


def test_memory_agent_policy_matches_runtime_docs():
    aura = _read("AURA.md")
    memory = _read(".MEMORY/06-ai-agents.md")
    protocol = json.loads(_read("PROTOCOL.json"))
    flow = _read(protocol["flow"]["file"])
    assert "first-ready" in memory
    assert "first-ready" in aura or "preflight readiness" in aura
    assert protocol["flow"]["current_version"] == "1.3.1"
    assert "t2me --dry-run" in flow
    assert "# Version: 1.3.1" in flow


def test_memory_contracts_note_legacy_ct_analyze_mapping():
    contracts_memory = _read(".MEMORY/02-contracts.md")
    protocol = json.loads(_read("PROTOCOL.json"))
    protocol_blob = json.dumps(protocol, ensure_ascii=False)
    assert "ct-analyze" in contracts_memory
    assert "ct-analyze" in protocol_blob


def test_first_read_docs_reference_active_runtime_surfaces():
    protocol = json.loads(_read("PROTOCOL.json"))
    active_flow_file = protocol["flow"]["file"]
    active_flow_version = protocol["flow"]["current_version"]

    agents = _read("AGENTS.md")
    contracts_readme = _read("contracts/README.md")
    viz_readme = _read("contracts/viz/README.md")
    movie_schedule = _read("contracts/viz/movie-schedule.md")
    analysis_result = _read("contracts/viz/analysis-result.md")

    for doc in (agents, contracts_readme, viz_readme):
        assert active_flow_file in doc
        assert active_flow_version in doc
        assert "./run" in doc

    assert "ct-cognize" in agents
    assert "ct-cognize" in contracts_readme
    assert "ct-cognize" in viz_readme
    assert "**Потребитель:** ct-cognize" in movie_schedule
    assert "**Производитель:** ct-cognize" in analysis_result


def test_owned_docs_only_keep_ct_analyze_when_marked_legacy():
    owned_docs = {
        "AGENTS.md": _read("AGENTS.md"),
        "contracts/README.md": _read("contracts/README.md"),
        "contracts/viz/README.md": _read("contracts/viz/README.md"),
        "contracts/viz/movie-schedule.md": _read("contracts/viz/movie-schedule.md"),
        "contracts/viz/analysis-result.md": _read("contracts/viz/analysis-result.md"),
    }

    for path, text in owned_docs.items():
        if "ct-analyze" in text:
            assert "legacy" in text.lower(), f"{path} must mark ct-analyze as legacy"
