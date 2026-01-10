PYTHON ?= python3
PYTHONPATH ?=
export PYTHONPATH := $(CURDIR):$(PYTHONPATH)
VENV ?= .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
SIM_DIR := simulations
SIM_SCRIPTS := $(filter-out $(SIM_DIR)/__init__.py $(SIM_DIR)/apply_watermarks.py $(SIM_DIR)/apply_low_fee_watermarks.py,$(wildcard $(SIM_DIR)/*.py))

.PHONY: api simulations simulation install install-venv install-deps

install-venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip

install-deps: install-venv
	$(VENV_PIP) install -e .
	@echo "Activate with: source $(VENV)/bin/activate"

install: install-deps

api:
	uvicorn api.main:app --reload --port 8001

simulations:
	@for script in $(SIM_SCRIPTS); do \
		echo "Running $$script"; \
		$(PYTHON) $$script; \
	done
	$(PYTHON) $(SIM_DIR)/apply_watermarks.py

simulation: simulations
