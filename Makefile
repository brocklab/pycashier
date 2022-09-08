VERSION := $(shell git describe --tags --dirty | sed -e 's/dirty/dev/g')


## lint | run pre-commit (black,isort,flake8)
.PHONY: lint
lint:
	pre-commit run --all

# target-check:
# 	@[ "${TARGET}" ] || \
# 		( echo ">> TARGET is not set";\
# 		  echo ">> options: all,wheel,docker";\
# 		  exit 1 )

# build: target-check
# 	$(MAKE) build-$(TARGET)

.PHONY: version-check
version-check:
	@if [[ "$(VERSION)" == *'-'* ]]; then\
		echo ">> version is invalid: $(VERSION)"; exit 1;\
	fi

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
	docker build --tag daylinmorgan/pycashier:$(VERSION) -f docker/Dockerfile .
	docker tag daylinmorgan/pycashier:$(VERSION) daylinmorgan/pycashier:latest

## push-docker | push docker tagged and latest docker image
.PHONY: push-docker
push-docker: version-check docker-build
	docker push daylinmorgan/pycashier:$(VERSION)
	docker push daylinmorgan/pycashier:latest

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

define USAGE ?=
==> {a.b_green}Pycashier Development Tasks{a.end} <==

{ansi.$(HEADER_COLOR)}usage{ansi.end}:
  make <recipe>

endef

-include .task.mk
$(if $(wildcard .task.mk),,.task.mk: ; curl -fsSL https://raw.githubusercontent.com/daylinmorgan/task.mk/v22.9.7/task.mk -o .task.mk)
