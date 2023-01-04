[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![PYPI][pypi-shield]][pypi-url]
[![PyVersion][pyversion-shield]][pyversion-url]
[![Conda][conda-shield]][conda-url]
[![ghcr.io][ghcrio-shield]][ghcrio-url]

# Pycashier

<img src="https://raw.githubusercontent.com/brocklab/pycashier/main/docs/demo.gif" alt="demo">

</br>
Tool for extracting and processing DNA barcode tags from Illumina sequencing.

Default parameters are designed for use by the [Brock Lab](https://github.com/brocklab) to process data generated from
[ClonMapper](https://docs.brocklab.com/clonmapper) lineage tracing experiments, but is extensible to other similarly designed tools.


### Bioconda Dependencies
- [cutadapt](https://github.com/marcelm/cutadapt) (sequence extraction)
- [starcode](https://github.com/gui11aume/starcode) (sequence clustering)
- [fastp](https://github.com/OpenGene/fastp) (merging/quality filtering)
- [pysam](https://github.com/pysam-developers/pysam) (sam file conversion to fastq)

### Pip/conda-forge Dependencies
- [rich](https://github.com/Textualize/rich)
- [click](https://github.com/pallets/click)
- [click-rich-help](https://github.com/daylinmorgan/click-rich-help)
- [tomlkit](https://github.com/sdispater/tomlkit)

## Installation
### Conda
You may use [conda](https://docs.conda.io/en/latest/)/[mamba](https://github.com/mamba-org/mamba) to install and manage the dependencies for this package.

```bash
conda install -c conda-forge -c bioconda cutadapt fastp pysam starcode pycashier
```

You can also use the included `env.yml` to create your environment and install everything you need.

```bash
conda env create -f https://raw.githubusercontent.com/brocklab/pycashier/main/env.yml
conda activate cashierenv
```

### Docker

If you prefer to use use `docker` you can use the below command.

```bash
docker run --rm -it -v $PWD:/data -u $(id -u):$(id -g) ghcr.io/brocklab/pycashier
```

### Pip (Not Recommended)

You may install with pip. Though it will be up to you to ensure all the
dependencies you would install from bioconda are on your path and installed correctly.
`Pycashier` will check for them before running.

```bash
pip install pycashier
```

## Usage

As of `v0.3.0` the interface of `pycashier` has changed. Previously a positional argument was used to indicate the source directory and additional flags would set the operation.
Now `pycashier` uses `click` and a series of commands.

As always use though use `pycashier --help` and additionally `pycashier <COMMAND> --help` for the full list of parameters.

See below for a brief explanation of each command.

### Extract

The primary use case of pycashier is extracting 20bp sequences from illumina generated fastq files.
This can be accomplished with the below command where `./fastqs` is a directory containing all of your fastq files.

```bash
pycashier extract -i ./fastqs
```

`Pycashier` will attempt to extract file names from your `.fastq` files using the first string delimited by a period.

For example:
- `sample1.fastq`: sample1
- `sample2.metadata_pycashier.will.ignore.fastq`: sample2

As `pycashier extract` runs, two directories will be generated `./pipeline` and `./outs`, configurable with `-p/--pipeline` and `-o/--output` respectively.

Your `pipeline` directory will contain all files and data generated while performing barcode extraction and clustering.
While `outs` will contain a single `.tsv` for each sample with the final barcode counts.

Expected output of `pycashier extract`:

```bash
fastqs
└── sample.raw.fastq
pipeline
├── qc
│   ├── sample.html
│   └── sample.json
├── sample.q30.barcode.fastq
├── sample.q30.barcodes.r3d1.tsv
├── sample.q30.barcodes.tsv
└── sample.q30.fastq
outs
└── sample.q30.barcodes.r3d1.min176_off1.tsv
```

*NOTE*: If you wish to provide `pycashier` with fastq files containing only your barcode you can supply the `--skip-trimming` flag.

### Merge

In some cases your data may be from paired-end sequencing. If you have two fastq files per sample
that overlap on the barcode region they can be combined with `pycashier merge`.
that overlap on the barcode region they can be combined with `pycashier merge`.


```bash
pycashier merge -i ./fastqgz
```

By default your output will be in `mergedfastqs`. Which you can then pass back to `pycashier` with `pycashier extract -i mergedfastqs`.

For single read, files are `<sample>.fastq` now they should both contain R1 and R2 and additionally may be gzipped.

For example:
- `sample.raw.R1.fastq.gz`,`sample.raw.R2.fastq.gz`: sample
- `sample.R1.fastq`,`sample.R2.fastq`: sample
- `sample.fastq`: fail, not R1 and R2


### Scrna

If your DNA barcodes are expressed and detectable in 10X 3'-based transcriptomic sequencing,
then you can extract these tags with `pycashier` and their associated umi/cell barcodes from the `cellranger` output.

For `pycashier scrna` we extract our reads from sam files.
This file can be generated using the output of `cellranger count`.
For each sample you would run:
```
samtools view -f 4 $CELLRANGER_COUNT_OUTPUT/sample1/outs/possorted_genome_bam.bam > sams/sample1.unmapped.sam
```
This will generate a sam file containing only the unmapped reads.

Then similar to normal barcode extraction you can pass a directory of these unmapped sam files to pycashier and extract barcodes. You can also still specify extraction parameters that will be passed to cutadapt as usual.

*Note*: The default parameters passed to cutadapt are unlinked adapters and minimum barcode length of 10 bp.

```
pycashier scrna -i sams
```

When finished the `outs` directory will have a `.tsv` containing the following columns: Illumina Read Info, UMI Barcode, Cell Barcode, gRNA Barcode

### Combine

This command can be used if you wish to generate a combined tsv from all files including headers and sample information.
By default it uses `./outs` for input and `./combined.tsv` for output.

## Config File

As of `v0.3.1` you may generate and supply `pycashier` with a toml config file using `-c/--config`.
The expected structure is each command followed by key value pairs of flags with hypens replaced by underscores:

```toml
[extract]
input = "fastqs"
threads = 10
unqualified_percent = 20

[merge]
input = "rawfastqgzs"
output = "mergedfastqs"
fastp_args = "-t 1"
```

The order of precedence for arguments is command line > config file > defaults.

For example if you were to use the above `pycashier.toml` with `pycashier extract -c pycashier.toml -t 15`.
The value used for threads would be 15.
You can confirm the parameter values as they will be printed prior to any execution.

For convenience, you can update/create your config file with `pycasher COMMAND --save-config [explicit|full]`.

"Explicit" will only save parameters already included in the config file or specified at runtime.
"Full" will include all parameters, again, maintaining preset values in config or specified at runtime.

## Non-Configurable Defaults

See below for the non-configurable flags provided to external tools in each command. Refer to their documentation regarding the purpose of these flags.

### Extract

- `fastp`: `--dont_eval_duplication`
- `cutadapt`: `--max-n=0 -n 2`

### Merge

- `fastp`: `-m -c -G -Q -L`

### Scrna

- `cutadapt`: `--max-n=0 -n 2`

## Usage notes
Pycashier will **NOT** overwrite intermediary files. If there is an issue in the process, please delete either the pipeline directory or the requisite intermediary files for the sample you wish to reprocess. This will allow the user to place new fastqs within the source directory or a project folder without reprocessing all samples each time.
- If there are reads from multiple lanes they should first be concatenated with `cat sample*R1*.fastq.gz > sample.R1.fastq.gz`
- Naming conventions:
    - Sample names are extracted from files using the first string delimited with a period. Please take this into account when naming sam or fastq files.
    - Each processing step will append information to the input file name to indicate changes, again delimited with periods.


## Acknowledgments

[Cashier](https://github.com/russelldurrett/cashier) is a tool developed by Russell Durrett for the analysis and extraction of expressed barcode tags.
This version like it's predecessor wraps around several command line bioinformatic tools to pull out expressed barcode tags.



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
