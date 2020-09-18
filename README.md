

# Cash in on Expressed Barcode Tags (EBTs) from NGS Sequencing Data *with Python*

[Cashier](https://github.com/russelldurrett/cashier) is a tool developed by Russell Durrett for the analysis and extraction of expressed barcode tags.

This python implementation offers the same flexibility and simple command line operation.

Like it's predecessor it is a wrapper for the tools cutadapt, fastx-toolkit, and starcode.

### Dependencies
- cutadapt
- starcode
- fastx-toolkit
- pear
- pysam

## Recommended Installation Procedure

```bash
git clone https://github.com/DaylinMorgan/pycashier.git
cd pycashier
conda env create -f cashier_env.yml
conda activate cashier_env
pip install .
```

Note: Conda is not required and all packages may be installed individually so long as they are on the path.

## Usage

Pycashier has one required argument which is the directory containing the fastq or sam files you wish to process.

```bash
cashier ./fastqs
```
For additional parameters see `cashier -h`.

As the files are processed two additional directories will be created `pipeline` and `outs`.

Currently all intermediary files generated as a result of the program will be found in `pipeline`.

While the final processed files will be found within the `outs` directory.

## Merging Files

Pycashier can now take paired end reads and perform a merging of the reads to produce a fastq which can then be used with cashier's default feature.
```bash
cashier ./fastqs -m
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
cashier ./unmapped_sams -sc 
```
When finished the `outs` directory will have a `.tsv` containing the following columns: Illumina Read Info, UMI Barcode, Cell Barcode, gRNA Barcode


## Usage notes
 Pycashier will **NOT** overwrite intermediary files. If there is an issue in the process please delete either the pipeline directory or the requisite intermediary files for the sample you wish to reprocess. This will allow the user to place new fastqs within the raw directory or a project folder without reprocessing all samples each time.
- Currently, cashiers expects to find `.fastq.gz` files when merging and `.fastq` files when extracting barcodes. This behavior may change in the future.
- If there are reads from multiple lanes they should first be concatenated with `cat sample*R1*.fastq.gz > sample.R1.fastq.gz`
- Naming conventions:
    - Samples names are extracted from files using the first string delimited with a period. Please take this into account when names sam or fastq files. 
    - Each processing step will append information to the input file name to indicate changes again delimited with periods. 

