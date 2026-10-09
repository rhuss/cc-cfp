.PHONY: validate install uninstall reinstall test test-hook lint-dashes clean help

MARKETPLACE := cc-cfp-marketplace
PLUGIN := cfp@$(MARKETPLACE)
VENV_PYTHON := $(HOME)/.venvs/cc-cfp/bin/python

validate:
	claude plugin validate ./
	claude plugin validate ./cfp/

install:
	@if claude plugin marketplace add ./ 2>&1 | grep -q "already installed"; then \
		echo "Updating marketplace..."; \
		claude plugin marketplace update $(MARKETPLACE); \
	else \
		echo "Marketplace added."; \
	fi
	@if claude plugin list 2>/dev/null | grep -q "$(PLUGIN)"; then \
		echo "Plugin already installed, reinstalling..."; \
		claude plugin rm $(PLUGIN) 2>/dev/null || true; \
	fi
	claude plugin install $(PLUGIN)

uninstall:
	@echo "Removing plugin..."
	@claude plugin rm $(PLUGIN) 2>/dev/null || echo "Plugin not installed"
	@echo "Removing marketplace..."
	@claude plugin marketplace rm $(MARKETPLACE) 2>/dev/null || echo "Marketplace not installed"

reinstall: uninstall install

test:
	@test -x "$(VENV_PYTHON)" || { echo "Dev venv missing. Run: uv venv ~/.venvs/cc-cfp && uv pip install --python ~/.venvs/cc-cfp/bin/python -r cfp/requirements-dev.txt"; exit 1; }
	$(VENV_PYTHON) -m pytest cfp/scripts/test -q

test-hook:
	@echo "Testing context-hook.py..."
	@echo '{"prompt":"/cfp:status","session_id":"test","cwd":"/tmp","hook_event_name":"UserPromptSubmit"}' | \
		python3 -I cfp/hooks/scripts/context-hook.py | tee /dev/stderr | grep -q "cfp-context"
	@echo "OK: hook emits <cfp-context>"

lint-dashes:
	@if rg -n --glob '!*.pyc' -e '\x{2014}' -e '\x{2013}' cfp $(wildcard README.md); then \
		echo "FAIL: em-dash or en-dash found"; exit 1; \
	else \
		echo "OK: no em-dash or en-dash characters"; \
	fi

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '.pytest_cache' -type d -prune -exec rm -rf {} +

help:
	@echo "Available targets:"
	@echo "  validate     - Validate plugin manifests"
	@echo "  install      - Install plugin (adds marketplace, installs/updates plugin)"
	@echo "  uninstall    - Remove plugin and marketplace"
	@echo "  reinstall    - Full uninstall and reinstall"
	@echo "  test         - Run pytest over cfp/scripts/test (needs ~/.venvs/cc-cfp)"
	@echo "  test-hook    - Pipe a /cfp:status prompt through the context hook"
	@echo "  lint-dashes  - Fail when em-dash or en-dash characters appear in cfp/ or README.md"
	@echo "  clean        - Remove Python caches"
