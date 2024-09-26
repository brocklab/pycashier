# Usage

Pycashier has 4 subcommands to facilitate barcode extraction from illumina sequencing:

- [extract](#extract): extract sequences from standard illumina reads
- [merge](#merge): merge overlapping sequences PE sequencings prior to extracting
- [receipt](#receipt): merge and summarize individual sample outputs of extract
- [scrna](#scrna): extract UMI/Cell labeled expressed barcode reads from 10X unmapped sam

All of the above commands can be configured using the appropriate [flags](/cli) or additionally a [config file](#config-file).

## Extract

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
└── sample.fastq
pipeline
├── pycashier.log
├── qc
│   ├── sample.html
│   └── sample.json
├── sample.q30.barcode.fastq
├── sample.q30.barcodes.r3d1.tsv
├── sample.q30.barcodes.tsv
└── sample.q30.fastq
outs
└── sample.q30.barcodes.r3d1.min12_off1.tsv
```

:::{note}
If you wish to provide `pycashier` with fastq files containing only your barcode you can supply the `--skip-trimming` flag.
:::

## Receipt

Following a successful run of `pycashier extract`, you can feed the outputs into `pycashier receipt` to combine the data into one `tsv` while
calculating the percent of total of each lineage within a sample. 
By default `pycashier` will also determine lineage overlap across samples.


## Merge

In some cases your data may be from paired-end sequencing. If you have two fastq files per sample
that overlap on the barcode region they can be combined with `pycashier merge`.


```bash
pycashier merge -i ./fastqgz
```

By default your output will be in `mergedfastqs`. Which you can then pass back to `pycashier` with `pycashier extract -i mergedfastqs`.

For single read inputs, files are `<sample>.fastq` now they should both contain R1 and R2.

For example:
- `sample.raw.R1.fastq.gz`,`sample.raw.R2.fastq.gz`: sample
- `sample.R1.fastq`,`sample.R2.fastq`: sample
- `sample.fastq`: fail, not R1 and R2


## Scrna

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


:::{note}
The default parameters passed to cutadapt are unlinked adapters and minimum barcode length of 10 bp.
:::

```
pycashier scrna -i sams
```

When finished the `outs` directory will have a `.tsv` containing the following columns: Illumina Read Info, UMI Barcode, Cell Barcode, gRNA Barcode.

:::{note}
This data can be noisy an it will be necessary to apply domain-specific ad-hoc filtering in order to confidently assign barcodes to cells.
Typically, this can be a achieved with a combination of UMI and cell doublet filtering.
:::

## Configuration

### Config File

You may generate and supply `pycashier` with a toml config file using `-c/--config`.
The expected structure is each command followed by key value pairs of flags with hypens replaced by underscores:

```toml
[global]
threads = 10
samples = "sample1,sample2,sample5"

[extract]
input = "fastqs"
unqualified_percent = 20

[merge]
input = "rawfastqgzs"
output = "mergedfastqs"
fastp_args = "-t 1"
```

You can also specify a global table as a fallback value for common flags such as `threads`.

:::{tip}
The order of precedence for arguments is command line > config file (command table) > config file (global table) > defaults.
:::

For example if you were to use the above `pycashier.toml` with `pycashier extract -c pycashier.toml -t 15`.
The value used for threads would be 15.
All non-default values will be printed prior to execution. You can view all parameters with `-v/--verbose`.

For convenience, you can update/create your config file with `pycasher COMMAND --save-config [explicit|full]`.
"Explicit" will only save parameters already included in the config file or specified at runtime.
"Full" will include all parameters, again, maintaining preset values in config or specified at runtime.

See the [cli reference](./cli.rst) for all options for each command.

### Executables

`Pycashier` depends on three executables (`cutadapt`, `starcode`, `fastp`) existing on your `$PATH`, you can force the use of a specific executable using environment variables of the form `PYCASHIER_<NAME>`.
For example to override the `cutadapt` used you could use something like the below command:

```sh
PYCASHIER_CUTADAPT="$HOME/important-software/cutadapt-v4" pycashier extract
```


## Caveats

Pycashier will **NOT** overwrite intermediary files. If there is an issue in the process,
please delete either the pipeline directory or the requisite intermediary files for the sample you wish to reprocess.
- If there are reads from multiple lanes they should first be concatenated with `cat sample*R1*.fastq.gz > sample.R1.fastq.gz`
- Naming conventions:
    - Sample names are extracted from files using the first string delimited with a period. Please take this into account when naming sam or fastq files.
    - Each processing step will append information to the input file name to indicate changes, again delimited with periods.
