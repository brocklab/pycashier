[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![PYPI][pypi-shield]][pypi-url]
[![PyVersion][pyversion-shield]][pyversion-url]
[![Conda][conda-shield]][conda-url]
[![ghcr.io][ghcrio-shield]][ghcrio-url]

# Pycashier

Tool for extracting and processing DNA barcode tags from Illumina sequencing.

Default parameters are designed for use by the [Brock Lab](https://github.com/brocklab) to process data generated from
[ClonMapper](https://docs.brocklab.com/clonmapper) lineage tracing experiments, but is extensible to other similarly designed tools.

## Documentation

See the [documentation](https://docs.brocklab.com/pycashier) for more in-depth installation and usage instructions.


## Getting Started

### Installation

#### Conda

You may use
[conda](https://docs.conda.io/en/latest/),
[mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html), or
[micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)
to install `pycashier` and it's runtime dependencies.

```bash
micromamba install bioconda::cutadapt bioconda::fastp bioconda::pysam bioconda::starcode conda-forge::pycashier
```

You can also use the included `env.yml` to create your environment and install everything you need.

```bash
wget https://raw.githubusercontent.com/brocklab/pycashier/main/conda/env.yml
micromamba create -f env.yml
micromamba activate cashierenv
```

Additionally, you may use [`pixi`](https://pixi.sh) to install and use pycashier.

```sh
pixi init --channel conda-forge --channel bioconda myproject
cd myproject
pixi add pycashier starcode pysam cutadapt fastp
pixi shell
```

#### Docker

If you prefer to use use `docker` you can use the below command.

```bash
docker run --rm -it -v $PWD:/data -u $(id -u):$(id -g) ghcr.io/brocklab/pycashier
```

> [!NOTE]
> You should specify a version tag with the image for better reproducibility for example, `ghrc.io/brocklab/pycashier:v2024.1001`.


### Usage

To extract barcodes from targeted sequencing data:

```sh
pycashier extract -i fastqs -o outs
```

To combine data from multiple samples and compute basic overlap metrics:

```sh
pycashier receipt -i outs -o combined.tsv
```

See `pycashier --help` and `pycashier SUBCMD --help` for additional subcommands and options.

---

`Pycashier` is open source and licensed under the [MIT License](https://github.com/brocklab/pycashier/blob/main/LICENSE).

[conda-shield]: https://img.shields.io/conda/vn/conda-forge/pycashier
[conda-url]: https://anaconda.org/conda-forge/pycashier
[pypi-shield]: https://img.shields.io/pypi/v/pycashier
[pypi-url]: https://pypi.org/project/pycashier/
[pyversion-url]: https://pypi.org/project/pycashier/
[pyversion-shield]: https://img.shields.io/badge/dynamic/json?query=info.requires_python&label=python&url=https%3A%2F%2Fpypi.org%2Fpypi%2Fpycashier%2Fjson
[ghcrio-shield]: https://img.shields.io/badge/ghcr.io-24292f?&logo=github&logoColor=white.svg
[ghcrio-url]: https://github.com/brocklab/pycashier/pkgs/container/pycashier
[forks-shield]: https://img.shields.io/github/forks/brocklab/pycashier.svg
[forks-url]: https://github.com/brocklab/pycashier/network/members
[stars-shield]: https://img.shields.io/github/stars/brocklab/pycashier.svg
[stars-url]: https://github.com/brocklab/pycashier/stargazers
[issues-shield]: https://img.shields.io/github/issues/brocklab/pycashier.svg
[issues-url]: https://github.com/brocklab/pycashier/issues
[license-shield]: https://img.shields.io/github/license/brocklab/pycashier.svg
[license-url]: https://github.com/brocklab/pycashier/blob/main/LICENSE
