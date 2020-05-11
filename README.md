

# Cash in on Expressed Barcode Tags (EBTs) from NGS Sequencing Data *with Python*

[Cashier](https://github.com/russelldurrett/cashier) is a tool developed by Russell Durrett for the analysis and extraction of expressed barcode tags.

This python implementation offers the same flexibility and simple command line operation.

Like it's predecessor it is a wrapper for the tools cutadapt, fastx-toolkit, and starcode.

### Dependencies
- cutadapt
- starcode
- fastx-toolkit


## Recommended Installation Procedure


```bash
git clone https://github.com/DaylinMorgan/pycashier.git
cd pycashier
pip install .
```

## Usage

Pycashier has one required argument which is the directory containing the fastq's you wish to process.

```bash
cashier ./fastqs
```
For additional parameters see `cashier -h`.

As the files are process two additional directories will be created `pipeline` and `outs`.

Currently all intermediary files generated as a result of the program will be found in `pipeline`.

While the final processed files will be found with the `outs` directory.

Pycashier will **NOT** overwrite intermediary files. If there is an issue in the process please delete either the pipeline directory or the requisite intermediary files for the sample you wish to reprocess. This will allow the user to place new fastqs within the raw directory or a project folder without reprocessing all samples each time.

