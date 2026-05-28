# Ionomegax Mersal Guard — integrated build
.PHONY: test verify run production-env enterprise-install docker-build build-all clean

PYTHON ?= python3
ROOT := $(CURDIR)

test:
	$(PYTHON) -m unittest discover -s tests -v

verify: test
	bash scripts/verify-build.sh

run:
	$(PYTHON) app.py

production-env:
	bash scripts/provision.sh mersal-guard.production.env
	@echo "Edit mersal-guard.production.env then: source mersal-guard.production.env && make run"

enterprise-install:
	bash scripts/mersal-complete-install.sh mersal-guard.env
	@echo "Edit mersal-guard.env secrets, then: source mersal-guard.env && make run"

docker-build:
	docker compose -f deploy/docker-compose.yml build

build-all:
	bash scripts/build-all.sh

clean:
	rm -rf data/*.sqlite3 data/tls/*.csr __pycache__ xig/__pycache__
