# ÖpenTrench labelling — VM-side detection server.
#
# `MODEL=<id>` selects which adapter the FastAPI app loads at startup.
# Only one model can be active at a time (one server process per port).
#
# Usage:
#   make grounding-dino       # serve Grounding DINO Base on :8000
#   make health               # curl localhost:8000/health
#   make stop                 # kill any running uvicorn server
#   make qwen-vl              # NOT IMPLEMENTED (stub adapter; will fail-load)

PORT ?= 8000
HOST ?= 0.0.0.0
IMAGE_ROOT ?= /home/threenicorn/data
UV ?= uv
PID_FILE := .server.pid

.PHONY: grounding-dino qwen-vl owlv2 florence2 t-rex2 health stop sync

sync:
	$(UV) sync

grounding-dino: sync stop
	MODEL=grounding-dino IMAGE_ROOT=$(IMAGE_ROOT) \
	    $(UV) run --no-sync uvicorn server.main:app --host $(HOST) --port $(PORT) \
	    > server.log 2>&1 & echo $$! > $(PID_FILE)
	@echo "started grounding-dino on $(HOST):$(PORT) (pid $$(cat $(PID_FILE))); tail -f server.log"

qwen-vl: sync stop
	MODEL=qwen-vl IMAGE_ROOT=$(IMAGE_ROOT) \
	    $(UV) run --no-sync uvicorn server.main:app --host $(HOST) --port $(PORT) \
	    > server.log 2>&1 & echo $$! > $(PID_FILE)
	@echo "started qwen-vl stub on $(HOST):$(PORT) (pid $$(cat $(PID_FILE))); tail -f server.log"

owlv2: sync stop
	MODEL=owlv2 IMAGE_ROOT=$(IMAGE_ROOT) \
	    $(UV) run --no-sync uvicorn server.main:app --host $(HOST) --port $(PORT) \
	    > server.log 2>&1 & echo $$! > $(PID_FILE)
	@echo "started owlv2 stub on $(HOST):$(PORT) (pid $$(cat $(PID_FILE)))"

florence2: sync stop
	MODEL=florence2 IMAGE_ROOT=$(IMAGE_ROOT) \
	    $(UV) run --no-sync uvicorn server.main:app --host $(HOST) --port $(PORT) \
	    > server.log 2>&1 & echo $$! > $(PID_FILE)
	@echo "started florence2 stub on $(HOST):$(PORT) (pid $$(cat $(PID_FILE)))"

t-rex2: sync stop
	MODEL=t-rex2 IMAGE_ROOT=$(IMAGE_ROOT) \
	    $(UV) run --no-sync uvicorn server.main:app --host $(HOST) --port $(PORT) \
	    > server.log 2>&1 & echo $$! > $(PID_FILE)
	@echo "started t-rex2 stub on $(HOST):$(PORT) (pid $$(cat $(PID_FILE)))"

health:
	@curl -sf http://localhost:$(PORT)/health | python3 -m json.tool

stop:
	@if [ -f $(PID_FILE) ]; then \
	    kill $$(cat $(PID_FILE)) 2>/dev/null || true ; rm -f $(PID_FILE) ; \
	    echo "stopped" ; \
	fi
	@pkill -f "uvicorn server.main" 2>/dev/null || true
