default:
  just --list

conda-env:
  mamba env create -f environment-dev.yml -p ./env --force

lint:
  pre-commit run --all

build target:
  just build-{{target }}

build-wheel:
  poetry build

build-docker:
  docker build --tag pycashier .
