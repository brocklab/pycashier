CURRENT_SHELL := $(shell echo $$SHELL)
SHELL = $(CURRENT_SHELL)
VERSION := $(shell git describe --tags --dirty)
CONDA_ACTIVATE = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate

.PHONY: $(MAKECMDGOALS)

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

build-all:
	$(MAKE) wheel
	$(MAKE) docker-build

wheel:
	poetry build

docker-build:
	docker build --tag daylinmorgan/pycashier:$(VERSION) .
	docker tag daylinmorgan/pycashier:$(VERSION) daylinmorgan/pycashier:latest

docker-push: version-check docker-build
	docker push daylinmorgan/pycashier:$(VERSION)
	docker push daylinmorgan/pycashier:latest


.ONESHELL:

conda-env: environment-dev.yml
	CONDA_ALWAYS_YES="true" mamba env create -f environment-dev.yml -p ./env --force

setup-env: conda-env
	$(CONDA_ACTIVATE) ./env
	poetry install
	pre-commit install
