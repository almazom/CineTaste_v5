# CineTaste v5.4.0 Makefile

.PHONY: test run dry-run clean help

# Default target
help:
	@echo "CineTaste v5.4.0 - Commands"
	@echo ""
	@echo "  make test        Run pytest test suite"
	@echo "  make test-cov    Run tests with coverage"
	@echo "  make test-net    Run optional live network tests"
	@echo "  make run         Run full pipeline (production)"
	@echo "  make dry-run     Run pipeline in preview mode"
	@echo "  make clean       Clean temp files"
	@echo "  make lint        Check code style"
	@echo ""

# Run tests
test:
	python3 -m pytest tests/ -v

# Run tests with coverage
test-cov:
	python3 -m pytest tests/ --cov=tools --cov-report=term-missing

# Run optional live-network tests
test-net:
	python3 -m pytest tests/ -m network -v

# Run full pipeline
run:
	./run --verbose

# Run pipeline in dry-run mode
dry-run:
	./run --dry-run --verbose

# Clean temp files
clean:
	rm -rf .testrun/*
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -name "*.pyc" -delete

# Lint check
lint:
	python3 -m py_compile tools/*/main.py tools/*/port.py tools/*/adapter_*.py
