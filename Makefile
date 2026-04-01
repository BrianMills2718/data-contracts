.PHONY: help status test test-quick check plan-sync agents-sync markdown-links

help:  ## Show available targets
	@grep -E '^[a-zA-Z0-9_.-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-16s %s\n", $$1, $$2}'

status:  ## Show git status
	@git status --short --branch

test:  ## Run full test suite
	@python -m pytest tests/ -v

test-quick:  ## Run tests quickly
	@python -m pytest -q

check:  ## Run tests, lint, and type checks
	@python -m pytest -q
	@ruff check src tests
	@mypy src

plan-sync:  ## Check plan index consistency
	@python scripts/meta/sync_plan_status.py --check

agents-sync:  ## Verify generated AGENTS.md is current
	@python scripts/meta/check_agents_sync.py --check

markdown-links:  ## Check local markdown links
	@python scripts/check_markdown_links.py --repo-root . README.md CLAUDE.md docs/plans/CLAUDE.md docs/plans/01_governed-baseline-and-capability-ownership-rollout.md docs/ops/CAPABILITY_DECOMPOSITION.md
