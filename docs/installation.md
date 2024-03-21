# Installation

## Runtime Dependencies
- [cutadapt](https://github.com/marcelm/cutadapt) (sequence extraction)
- [starcode](https://github.com/gui11aume/starcode) (sequence clustering)
- [fastp](https://github.com/OpenGene/fastp) (merging/quality filtering)
- [pysam](https://github.com/pysam-developers/pysam) (sam file conversion to fastq)

## Conda

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


## Docker

If you prefer to use use `docker` you can use the below command.

```bash
docker run --rm -it -v $PWD:/data -u $(id -u):$(id -g) ghcr.io/brocklab/pycashier
```

:::{note}
You should specify a version tag with the image for better reproducibility for example, `ghrc.io/brocklab/pycashier:v2024.1001`.
:::

## Pip (Not Recommended)

You may install with pip. Though it will be up to you to ensure all the
dependencies you would install from bioconda are on your path and installed correctly.
At a minimum, `pycashier` should check that any dependencies are available on the PATH.
However, it will not verify the versions installed are sufficiently recent.

```bash
pip install pycashier
```

