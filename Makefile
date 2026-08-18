# Oh-My-Research — common format / lint targets (macOS + Linux)
#
# Tools (install as needed):
#   ruff      — Python format + lint   (pip install ruff / uv tool install ruff)
#   prettier  — JSON / YAML / Markdown (npm install -g prettier)
#   jq        — optional JSON pretty-print fallback
#
# Usage:
#   make help
#   make format
#   make check

.PHONY: help format format-python format-json format-yaml format-md \
	lint check format-check install-format-tools

PYTHON ?= python3
RUFF ?= ruff
PRETTIER ?= prettier

# Skill package + any future top-level scripts
PYTHON_PATHS := skills

# JSON / YAML / Markdown under the repo (exclude caches / venvs)
FIND_PRUNE := \( -path './.git/*' -o -path './.venv/*' -o -path './venv/*' \
	-o -path '*/__pycache__/*' -o -path './.ruff_cache/*' -o -path './.soothe/*' \
	-o -path '*/node_modules/*' \) -prune

JSON_FILES = $(shell find . $(FIND_PRUNE) -o -type f -name '*.json' -print | sort)
YAML_FILES = $(shell find . $(FIND_PRUNE) -o -type f \( -name '*.yml' -o -name '*.yaml' \) -print | sort)
MD_FILES   = $(shell find . $(FIND_PRUNE) -o -type f -name '*.md' -print | sort)

help: ## Show available targets
	@echo "Oh-My-Research format targets"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Tools: $(RUFF), $(PRETTIER) (optional for yaml/md), jq (optional JSON fallback)"

format: format-python format-json format-yaml ## Format Python, JSON, and YAML

format-python: ## Format Python with ruff (format + import sort)
	@command -v $(RUFF) >/dev/null || { echo "ruff not found. Try: make install-format-tools"; exit 1; }
	$(RUFF) format $(PYTHON_PATHS)
	$(RUFF) check --select I --fix $(PYTHON_PATHS)

format-json: ## Pretty-print JSON (prettier, else jq, else python json)
	@files="$(JSON_FILES)"; \
	if [ -z "$$files" ]; then echo "No JSON files."; exit 0; fi; \
	if command -v $(PRETTIER) >/dev/null 2>&1; then \
		$(PRETTIER) --write --parser json $$files; \
	elif command -v jq >/dev/null 2>&1; then \
		for f in $$files; do \
			tmp=$$(mktemp); \
			jq --indent 2 . "$$f" > "$$tmp" && mv "$$tmp" "$$f"; \
		done; \
		echo "Formatted JSON with jq."; \
	else \
		$(PYTHON) -c "\
from pathlib import Path; import json, sys;\
files = sys.argv[1:];\
\
for raw in files:\
    path = Path(raw);\
    data = json.loads(path.read_text(encoding='utf-8'));\
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8');\
    print(path);\
" $$files; \
	fi

format-yaml: ## Format YAML with prettier (no-op if no files / tool)
	@files="$(YAML_FILES)"; \
	if [ -z "$$files" ]; then echo "No YAML files."; exit 0; fi; \
	if command -v $(PRETTIER) >/dev/null 2>&1; then \
		$(PRETTIER) --write $$files; \
	else \
		echo "prettier not found; skip YAML. Install: npm install -g prettier"; \
		exit 1; \
	fi

format-md: ## Format Markdown with prettier (optional)
	@files="$(MD_FILES)"; \
	if [ -z "$$files" ]; then echo "No Markdown files."; exit 0; fi; \
	command -v $(PRETTIER) >/dev/null 2>&1 || { echo "prettier not found"; exit 1; }
	$(PRETTIER) --write --prose-wrap preserve $$files

lint: ## Lint Python with ruff
	@command -v $(RUFF) >/dev/null || { echo "ruff not found. Try: make install-format-tools"; exit 1; }
	$(RUFF) check $(PYTHON_PATHS)

check: format-check lint ## CI: verify Python format + lint (no write)
format-check: ## Check Python formatting without writing
	@command -v $(RUFF) >/dev/null || { echo "ruff not found. Try: make install-format-tools"; exit 1; }
	$(RUFF) format --check $(PYTHON_PATHS)
	$(RUFF) check --select I $(PYTHON_PATHS)

install-format-tools: ## Install ruff (pip) — prettier is npm: npm i -g prettier
	$(PYTHON) -m pip install -U ruff
	@echo "Optional: npm install -g prettier   # JSON/YAML/Markdown"
	@echo "Optional: jq                        # JSON fallback (apt/brew)"
