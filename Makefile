VERSION := $(shell git describe --tags --dirty | sed -e 's/dirty/dev/g')


## lint | run pre-commit (black,isort,flake8)
.PHONY: lint
lint:
	pre-commit run --all

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
	docker build --tag brocklab/pycashier:$(VERSION) -f docker/Dockerfile .
	docker tag brocklab/pycashier:$(VERSION) brocklab/pycashier:latest

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




define USAGE ?=
==> {a.b_green}Pycashier Development Tasks{a.end} <==

{ansi.$(HEADER_COLOR)}usage{ansi.end}:
  make <recipe>

endef

-include .task.mk
$(if $(wildcard .task.mk),,.task.mk: ; curl -fsSL https://raw.githubusercontent.com/daylinmorgan/task.mk/v22.9.7/task.mk -o .task.mk)
