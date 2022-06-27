CURRENT_SHELL := $(shell echo $$SHELL)
SHELL = $(CURRENT_SHELL)
VERSION := $(shell git describe --tags --dirty)
CONDA_ACTIVATE = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate

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
	poetry build

## build and tag docker image with version
docker-build:
	docker build --tag daylinmorgan/pycashier:$(VERSION) .
	docker tag daylinmorgan/pycashier:$(VERSION) daylinmorgan/pycashier:latest

## push docker tagged and latest docker image
docker-push: version-check docker-build
	docker push daylinmorgan/pycashier:$(VERSION)
	docker push daylinmorgan/pycashier:latest


.ONESHELL:

conda-env: environment-dev.yml
	CONDA_ALWAYS_YES="true" mamba env create -f environment-dev.yml -p ./env --force

## setup conda env with poetry/pre-commit
setup-env: conda-env
	$(CONDA_ACTIVATE) ./env
	poetry install
	pre-commit install

FILL = 15
## Display this help screen
help:
	@awk '/^[a-z.A-Z_-]+:/ { helpMessage = match(lastLine, /^##(.*)/); \
    if (helpMessage) { helpCommand = substr($$1, 0, index($$1, ":")-1); \
    helpMessage = substr(lastLine, RSTART + 3, RLENGTH); printf "\033[36m%-$(FILL)s\033[0m%s\n"\
    , helpCommand, helpMessage;}} { lastLine = $$0 }' $(MAKEFILE_LIST)
