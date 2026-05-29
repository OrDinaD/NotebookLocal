PYTHON ?= python3

.PHONY: install run test lint smoke reindex

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	streamlit run app/streamlit_app.py

test:
	pytest -q

lint:
	$(PYTHON) -m py_compile app/*.py ingestion/*.py retrieval/*.py models/*.py storage/*.py

smoke:
	$(PYTHON) scripts/smoke_ingest.py

reindex:
	$(PYTHON) scripts/reindex.py
