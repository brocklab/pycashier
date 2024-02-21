VERSION ?= $(shell git describe --tags --dirty='-dev')

checks: lint types ## run lint,types

lint: ## run pre-commit (ruff lint/format)
	$(call msg,Linting w/ Pre-commit)
	@pre-commit run --all || pre-commit run --all

types: ## typecheck with mypy
	$(call msg,Typechecking w/ Mypy)
	@mypy src/pycashier/ tests/

test: ## run test w/ pytest
	$(call msg, Testing w/ Pytest)
	@pytest tests/ --cov=src/pycashier

build: ## build-{dist,docker}
	$(MAKE) build-dist
	$(MAKE) build-docker

build-dist: ## make wheel & source distribution
	pdm build

## build-docker |> build and tag docker image with version
build-docker: docker/prod.lock
	docker build --tag ghcr.io/brocklab/pycashier:$(VERSION) -f docker/Dockerfile .
	docker tag ghcr.io/brocklab/pycashier:$(VERSION) pycashier:latest

docker/%.lock: docker/%.yml
	docker run -it --rm -v $$(pwd):/tmp -u $$(id -u):$$(id -g) mambaorg/micromamba:0.24.0 \
   /bin/bash -c "micromamba create --yes --name env --file $< && \
      micromamba env export --name env --explicit > $@"

docs: ## build docs
	sphinx-build docs site

docs-serve: ## serve live docs
	sphinx-autobuild docs site --port 8234

## env |> bootstrap conda/pdm/pre-commit
env: conda-env setup-env

conda-env: conda/env-dev.yml ##
	micromamba env create -f $< -p ./env

setup-env: ##
	micromamba run -p ./env pdm install
	micromamba run -p ./env pre-commit install

.PHONY: version-check
version-check:
	@if [[ "$(VERSION)" == *'-'* ]]; then\
		echo ">> version is invalid: $(VERSION)"; exit 1;\
	fi

PHONIFY = true
USAGE = ==> {a.b_green}Pycashier Development Tasks{a.end} <==\n
msg = $(if $(tprint),$(call tprint,{a.bold}==>{a.cyan} $(1){a.end}),@echo '==> $(1)')
-include .task.mk
$(if $(wildcard .task.mk),,.task.mk: ; curl -fsSL https://raw.githubusercontent.com/daylinmorgan/task.mk/v23.1.2/task.mk -o .task.mk)
