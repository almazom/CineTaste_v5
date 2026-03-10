# CineTaste v5.5.0 Makefile
# ==========================
# Rich E2E Integration Test Suite with Transparency & Visualization

.PHONY: help test test-cov test-net test-e2e test-e2e-verbose test-e2e-html \
        run dry-run clean lint e2e-dashboard e2e-latest

# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────

help:
	@echo "╔══════════════════════════════════════════════════════════════════════════╗"
	@echo "║  CineTaste v5.5.0 — Integration Test Suite                               ║"
	@echo "╠══════════════════════════════════════════════════════════════════════════╣"
	@echo "║  UNIT TESTS                                                              ║"
	@echo "║    make test           Run pytest test suite                             ║"
	@echo "║    make test-cov       Run tests with coverage report                    ║"
	@echo "║    make test-net       Run network integration tests                     ║"
	@echo "║                                                                            ║"
	@echo "║  E2E INTEGRATION TESTS                                                   ║"
	@echo "║    make test-e2e       Run E2E suite with rich transparency              ║"
	@echo "║    make test-e2e-verbose  Run E2E with detailed step output              ║"
	@echo "║    make test-e2e-html  Run E2E and generate HTML report                  ║"
	@echo "║    make e2e-dashboard  Open latest HTML report in browser                ║"
	@echo "║    make e2e-latest     Show latest E2E run summary                       ║"
	@echo "║                                                                            ║"
	@echo "║  PIPELINE                                                                ║"
	@echo "║    make run            Run full pipeline (production)                    ║"
	@echo "║    make dry-run        Run pipeline in preview mode                      ║"
	@echo "║                                                                            ║"
	@echo "║  MAINTENANCE                                                             ║"
	@echo "║    make clean          Clean temp files and artifacts                    ║"
	@echo "║    make clean-e2e      Clean E2E reports only                            ║"
	@echo "║    make lint           Check code style                                  ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════╝"

# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

test:
	@echo "▶ Running unit tests..."
	python3 -m pytest tests/ -v

test-cov:
	@echo "▶ Running tests with coverage..."
	python3 -m pytest tests/ --cov=tools --cov-report=term-missing --cov-report=html:reports/coverage-html
	@echo "✓ Coverage report: reports/coverage-html/index.html"

test-net:
	@echo "▶ Running network integration tests..."
	python3 -m pytest tests/ -m network -v

# ─────────────────────────────────────────────────────────────────────────────
# E2E Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

test-e2e:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════╗"
	@echo "║  E2E Integration Test Suite — Phase 7.5                                  ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	python3 tests/e2e_runner.py

test-e2e-verbose:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════╗"
	@echo "║  E2E Integration Test Suite — Verbose Mode                               ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	python3 tests/e2e_runner.py --verbose

test-e2e-html:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════╗"
	@echo "║  E2E Integration Test Suite — HTML Report Generation                     ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@mkdir -p reports/e2e
	python3 tests/e2e_runner.py --verbose
	@echo ""
	@echo "▶ Generating HTML report..."
	@LATEST_JSON=$$(ls -t reports/e2e/e2e-report-*.json 2>/dev/null | head -1) && \
	if [ -n "$$LATEST_JSON" ]; then \
		python3 tests/e2e_html_report.py "$$LATEST_JSON"; \
		echo ""; \
		echo "✓ HTML report generated: reports/e2e/$$(basename $$LATEST_JSON .json).html"; \
		echo "✓ Open with: make e2e-dashboard"; \
	else \
		echo "✗ No E2E report found. Run 'make test-e2e' first."; \
		exit 1; \
	fi

test-e2e-golden:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════╗"
	@echo "║  E2E Golden Paths Only                                                   ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	python3 tests/e2e_runner.py --filter golden

test-e2e-boundary:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════╗"
	@echo "║  E2E Boundary Cases Only                                                 ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	python3 tests/e2e_runner.py --filter boundary

test-e2e-recovery:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════╗"
	@echo "║  E2E Recovery Paths Only                                                 ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	python3 tests/e2e_runner.py --filter recovery

# ─────────────────────────────────────────────────────────────────────────────
# E2E Reports & Dashboard
# ─────────────────────────────────────────────────────────────────────────────

e2e-dashboard:
	@LATEST_HTML=$$(ls -t reports/e2e/e2e-report-*.html 2>/dev/null | head -1) && \
	if [ -n "$$LATEST_HTML" ]; then \
		echo "▶ Opening dashboard: $$LATEST_HTML"; \
		xdg-open "$$LATEST_HTML" 2>/dev/null || open "$$LATEST_HTML" 2>/dev/null || \
		echo "✓ Open manually: $$LATEST_HTML"; \
	else \
		echo "✗ No HTML report found. Run 'make test-e2e-html' first."; \
		exit 1; \
	fi

e2e-latest:
	@python3 tests/e2e_summary.py

e2e-history:
	@python3 tests/e2e_summary.py history

# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

run:
	@echo "▶ Running full pipeline (production)..."
	./run --verbose

dry-run:
	@echo "▶ Running pipeline in dry-run mode..."
	./run --dry-run --verbose

# ─────────────────────────────────────────────────────────────────────────────
# Maintenance
# ─────────────────────────────────────────────────────────────────────────────

clean:
	@echo "▶ Cleaning temp files..."
	rm -rf .testrun/*
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -name "*.pyc" -delete
	rm -rf reports/coverage-html
	@echo "✓ Clean complete"

clean-e2e:
	@echo "▶ Cleaning E2E reports..."
	rm -rf reports/e2e/*
	@echo "✓ E2E reports cleaned"

lint:
	@echo "▶ Checking code style..."
	python3 -m py_compile tools/*/main.py tools/*/port.py tools/*/adapter_*.py tests/*.py
	@echo "✓ Lint passed"

# ─────────────────────────────────────────────────────────────────────────────
# Quick Aliases
# ─────────────────────────────────────────────────────────────────────────────

t: test
tc: test-cov
e2e: test-e2e
e2e-v: test-e2e-verbose
e2e-h: test-e2e-html
dash: e2e-dashboard
latest: e2e-latest
