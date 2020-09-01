

# Cash in on Expressed Barcode Tags (EBTs) from NGS Sequencing Data *with Python*

[Cashier](https://github.com/russelldurrett/cashier) is a tool developed by Russell Durrett for the analysis and extraction of expressed barcode tags.

This python implementation offers the same flexibility and simple command line operation.

Like it's predecessor it is a wrapper for the tools cutadapt, fastx-toolkit, and starcode.

### Dependencies
- cutadapt
- starcode
- fastx-toolkit
- pear

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

Pycashier has one required argument which is the directory containing the fastq's you wish to process.

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
## Usage notes
 Pycashier will **NOT** overwrite intermediary files. If there is an issue in the process please delete either the pipeline directory or the requisite intermediary files for the sample you wish to reprocess. This will allow the user to place new fastqs within the raw directory or a project folder without reprocessing all samples each time.
- Currently, cashiers expects to find `.fastq.gz` files when merging and `.fastq` files when extracting barcodes. This behavior may change in the future.
- If there are reads from multiple lanes they should first be concatenated with `cat sample*R1*.fastq.gz > sample.R1.fastq.gz`
