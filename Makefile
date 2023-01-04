VERSION := $(shell git describe --tags --dirty='-dev')

## checks | run lint,types
.PHONY: checks
checks: lint types

## lint | run pre-commit (black,isort,flake8)
.PHONY: lint
lint:
	$(call msg,Linting w/ Pre-commit)
	@pre-commit run --all || pre-commit run --all

## types | typecheck with mypy
.PHONY: types
types:
	$(call msg,Typechecking w/ Mypy)
	@mypy pycashier/ tests/

## test | run test w/ pytest
.PHONY: test
test:
	$(call msg, Testing w/ Pytest)
	@pytest tests/

## build | build-{dist,docker}
.PHONY: build
build:
	$(MAKE) build-dist
	$(MAKE) build-docker

## build-dist | make wheel & source distribution
.PHONY: build-dist
build-dist:
	pdm build

## build-docker | build and tag docker image with version
.PHONY: build-docker
build-docker: docker/prod.lock
	docker build --tag ghcr.io/brocklab/pycashier:$(VERSION) -f docker/Dockerfile .
	docker tag ghcr.io/brocklab/pycashier:$(VERSION) pycashier:latest

docker/%.lock: docker/%.yml
	docker run -it --rm -v $$(pwd):/tmp -u $$(id -u):$$(id -g) mambaorg/micromamba:0.24.0 \
   /bin/bash -c "micromamba create --yes --name env --file $< && \
      micromamba env export --name env --explicit > $@"

## env | bootstrap conda/pdm/pre-commit
.PHONY: env
env: conda-env setup-env

conda-env: env-dev.yml
	mamba env create -f $< -p ./env --force

setup-env:
	mamba run -p ./env pdm install
	mamba run -p ./env pre-commit install

.PHONY: version-check
version-check:
	@if [[ "$(VERSION)" == *'-'* ]]; then\
		echo ">> version is invalid: $(VERSION)"; exit 1;\
	fi


USAGE = ==> {a.b_green}Pycashier Development Tasks{a.end} <==\n
msg = $(if $(tprint),$(call tprint,{a.bold}==>{a.cyan} $(1){a.end}),@echo '==> $(1)')
-include .task.mk
$(if $(filter help,$(MAKECMDGOALS)),$(if $(wildcard .task.mk),,.task.mk: ; curl -fsSL https://raw.githubusercontent.com/daylinmorgan/task.mk/v22.9.28/task.mk -o .task.mk))
