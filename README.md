# Cash in on Expressed Barcode Tags (EBTs) from NGS Sequencing Data *with Python*

Tool for extracting and processing DNA barcode tags from Illumina sequencing.

Default parameters are designed for use by the Brock Lab to process data generated from
ClonMapper lineage tracing experiments, but is extensible to other similarly designed tools.


### Bioconda Dependencies
- cutadapt (sequence extraction)
- starcode (sequence clustering)
- fastx-toolkit (PHred score filtering)
- pear (paired end read merging)
- pysam (sam file convertion to fastq)

## Installation
It's recommended to use [conda](https://docs.conda.io/en/latest/)/[mamba](https://github.com/mamba-org/mamba) to install and manage the dependencies for this package

```bash
conda install -c bioconda cutadapt fastx-toolkit pear pysam starcode
conda install -c conda-forge pycashier
```

You can also use the included `environment.yml` to create your environment and install everything you need.

```bash
conda env create -f https://raw.githubusercontent.com/brocklab/pycashier/main/environment.yml
conda activate cashierenv
```

Additionally you may install with pip. Though it will be up to you to ensure all the
dependencies you would install from bioconda are on your path and installed correctly.
`Pycashier` will check for them before running.

```bash
pip install pycashier
```

## Usage

Pycashier has one required argument which is the directory containing the fastq or sam files you wish to process.

```bash
conda activate cashierenv
pycashier ./fastqs
```
For additional parameters see `pycashier -h`.

As the files are processed two additional directories will be created `pipeline` and `outs`.

**Note**: these can be specified with `-pd/--pipelinedir` and  `-o/--outdir`.

Currently all intermediary files generated as a result of the program will be found in `pipeline`.

While the final processed files will be found within the `outs` directory.

## Merging Files

Pycashier can now take paired end reads and perform a merging of the reads to produce a fastq which can then be used with pycashier's default feature.
```bash
pycashier ./fastqs -m
```

## Processing Barcodes from 10X bam files

Pycashier can also extract gRNA barcodes along with 10X cell and umi barcodes.

Firstly we are only interested in the unmapped reads. From the cellranger bam output you would obtain these reads using samtools.

```
samtools view -f 4 possorted_genome_bam.bam > unmapped.sam
```

Then similar to normal barcode extraction you can pass a directory of these unmapped sam files to pycashier and extract barcodes. You can also still specify extraction parameters that will be passed to cutadapt as usual.

*Note*: The default parameters passed to cutadapt are unlinked adapters and minimum barcode length of 10 bp.

```
pycashier ./unmapped_sams -sc
```
When finished the `outs` directory will have a `.tsv` containing the following columns: Illumina Read Info, UMI Barcode, Cell Barcode, gRNA Barcode


## Usage notes
Pycashier will **NOT** overwrite intermediary files. If there is an issue in the process, please delete either the pipeline directory or the requisite intermediary files for the sample you wish to reprocess. This will allow the user to place new fastqs within the source directory or a project folder without reprocessing all samples each time.
- Currently, pycashier expects to find `.fastq.gz` files when merging and `.fastq` files when extracting barcodes. This behavior may change in the future.
- If there are reads from multiple lanes they should first be concatenated with `cat sample*R1*.fastq.gz > sample.R1.fastq.gz`
- Naming conventions:
    - Sample names are extracted from files using the first string delimited with a period. Please take this into account when naming sam or fastq files.
    - Each processing step will append information to the input file name to indicate changes, again delimited with periods.


## Acknowledgments

[Cashier](https://github.com/russelldurrett/cashier) is a tool developed by Russell Durrett for the analysis and extraction of expressed barcode tags.
This version like it's predecessor wraps around several command line bioinformatic tools to pull out expressed barcode tags.
