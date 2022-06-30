CURRENT_SHELL := $(shell echo $$SHELL)
SHELL = $(CURRENT_SHELL)
VERSION := $(shell git describe --tags --dirty | sed -e 's/dirty/dev/g')
CONDA = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ;

.PHONY: $(MAKECMDGOALS)

## lint w/pre-commit
lint:
	pre-commit run --all

# target-check:
# 	@[ "${TARGET}" ] || \
# 		( echo ">> TARGET is not set";\
# 		  echo ">> options: all,wheel,docker";\
# 		  exit 1 )

# build: target-check
# 	$(MAKE) build-$(TARGET)

version-check:
	@if [[ "${VERSION}" == *'-'* ]];then\
		echo ">> version is invalid: $(VERSION)"; exit 1;\
	fi

## build wheel & docker images
build-all:
	$(MAKE) wheel
	$(MAKE) docker-build

## build wheel
wheel:
	pdm build

## build and tag docker image with version
docker-build: docker/prod.lock
	docker build --tag daylinmorgan/pycashier:$(VERSION) -f docker/Dockerfile .
	docker tag daylinmorgan/pycashier:$(VERSION) daylinmorgan/pycashier:latest

## push docker tagged and latest docker image
docker-push: version-check docker-build
	docker push daylinmorgan/pycashier:$(VERSION)
	docker push daylinmorgan/pycashier:latest

docker/%.lock: docker/%.yml
	docker run -it --rm -v $$(pwd):/tmp -u $$(id -u):$$(id -g) mambaorg/micromamba:0.24.0 \
   /bin/bash -c "micromamba create --yes --name env --file $< && \
                 micromamba env export --name env --explicit > $@"

.PHONY: env conda-env setup-env
.ONESHELL: env conda-env setup-env

env: conda-env setup-env

conda-env: env-dev.yml
	$(CONDA) CONDA_ALWAYS_YES="true" mamba env create -f env-dev.yml -p ./env --force

## setup conda env with poetry/pre-commit
setup-env:
	$(CONDA) conda activate ./env
	pdm install
	pdm plugin add pdm-shell
	pdm config --local python.use_venv true
	pdm run pre-commit install

FILL = 15
## Display this help screen
help:
	@awk '/^[a-z.A-Z_-]+:/ { helpMessage = match(lastLine, /^##(.*)/); \
    if (helpMessage) { helpCommand = substr($$1, 0, index($$1, ":")-1); \
    helpMessage = substr(lastLine, RSTART + 3, RLENGTH); printf "\033[36m%-$(FILL)s\033[0m%s\n"\
    , helpCommand, helpMessage;}} { lastLine = $$0 }' $(MAKEFILE_LIST)

test-mamba:
	# CONDA_ALWAYS_YES="true" mamba
	CONDA_ALWAYS_YES="true" mamba env create -f environment-dev.yml -p ./env --force
