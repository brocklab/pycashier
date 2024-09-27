=============
CLI Reference
=============

pycashier 
----------------------------------


.. tab:: image

  .. image:: svgs/pycashier.svg

.. tab:: plaintext

  .. code-block::

      Usage: pycashier [OPTIONS] COMMAND [ARGS]...

        Cash in on DNA Barcode Tags

        See `pycashier COMMAND -h` for more information.

      Options:
        --version   Show the version and exit.
        -h, --help  Show this message and exit.

      Commands:
        extract  extract DNA barcodes from a directory of fastq files
        merge    merge overlapping paired-end reads using fastp
        receipt  combine and summarize outputs of extract
        scrna    extract expressed DNA barcodes from scRNA-seq



pycashier extract
----------------------------------


.. tab:: image

  .. image:: svgs/pycashier-extract.svg

.. tab:: plaintext

  .. code-block::

      Usage: pycashier extract [OPTIONS]

        extract DNA barcodes from a directory of fastq files

        Sample names should be delimited with a ".", such as `<sample>.raw.fastq`,
        anything succeeding the first period will be ignored by `pycashier`.

        If your data is paired-end with overlapping barcodes, see `pycashier merge`.

      Input/Output Options:
        -i, --input DIRECTORY     source directory containing fastq files [required]
        -o, --output DIRECTORY    output directory [default: ./outs]
        -p, --pipeline DIRECTORY  pipeline directory [default: ./pipeline]
        -s, --samples TEXT        comma separated list of samples to process

      Quality (Fastp) Options:
        -q, --quality INTEGER           minimum PHRED quality for filtering reads [default: 30]
        -up, --unqualified-percent INTEGER
                                        minimum percent of bases which can be below quality threshold
                                        [default: 20]
        -fa, --fastp-args TEXT          additional arguments passed to fastp [default:
                                        --dont_eval_duplication]

      Trim (Cutadapt) Options:
        -ca, --cutadapt-args TEXT       additional arguments passed to cutadapt [default: --max-n=0 -n 2
                                        --trimmed-only]
        -e, --error FLOAT               error tolerance supplied to cutadapt [default: 0.1]
        -l, --length INTEGER            target length of extracted barcode [default: 20]
        -ua, --upstream-adapter TEXT    5' sequence flanking barcode
        -da, --downstream-adapter TEXT  3' sequence flanking barcode
        --unlinked-adapters             run cutadapt using unlinked adapters
        --skip-trimming                 skip cutadapt trimming entirely and use reads as-is

      Cluster (Starcode) Options:
        -r, --ratio INTEGER           ratio to use for message passing clustering [default: 3]
        -d, --distance INTEGER RANGE  levenshtein distance for clustering [default: 1; 1<=x<=8]

      Filter Options:
        -fc, --filter-count INTEGER  minium nominal number of reads
        -fp, --filter-percent FLOAT  minimum percentage of total reads [default: 0.005]
        --offset INTEGER             length offset from target barcode length post-clustering [default: 1]

      General Options:
        -t, --threads INTEGER          number of cpu cores to use [default: 1]
        -y, --yes                      answer yes to prompts
        -v, --verbose                  show more output, set log level to debug
        -c, --config FILE              read parameter values from config file [default: pycashier.toml]
        --save-config [explicit|full]  save current params to file specified by `--config`
        --log-file FILE                path to log file [default: <pipeline-dir>/pycashier.log] 
        -h, --help                     Show this message and exit.



pycashier merge
----------------------------------


.. tab:: image

  .. image:: svgs/pycashier-merge.svg

.. tab:: plaintext

  .. code-block::

      Usage: pycashier merge [OPTIONS]

        merge overlapping paired-end reads using fastp

        Simple wrapper over `fastp` to combine R1 and R2 from PE fastq files.

      Input/Output Options:
        -i, --input DIRECTORY     source directory containing gzipped R1 and R2 fastq files [required]
        -o, --output DIRECTORY    output directory [default: ./mergedfastqs]
        -p, --pipeline DIRECTORY  pipeline directory [default: ./pipeline]
        -s, --samples TEXT        comma separated list of samples to process

      Merge Options:
        -fa, --fastp-args TEXT  additional arguments passed to fastp [default: -m -c -G -Q -L]

      General Options:
        -t, --threads INTEGER          number of cpu cores to use [default: 1]
        -y, --yes                      answer yes to prompts
        -v, --verbose                  show more output, set log level to debug
        -c, --config FILE              read parameter values from config file [default: pycashier.toml]
        --save-config [explicit|full]  save current params to file specified by `--config`
        --log-file FILE                path to log file [default: <pipeline-dir>/pycashier.log] 
        -h, --help                     Show this message and exit.



pycashier receipt
----------------------------------


.. tab:: image

  .. image:: svgs/pycashier-receipt.svg

.. tab:: plaintext

  .. code-block::

      Usage: pycashier receipt [OPTIONS]

        combine and summarize outputs of extract

      Input/Output Options:
        -i, --input DIRECTORY     source directory containing sam files from scRNA-seq [default: ./outs;
                                  required]
        -o, --output FILE         combined tsv of all samples found in input directory [default:
                                  ./combined.tsv]
        -p, --pipeline DIRECTORY  pipeline directory [default: ./pipeline]
        -s, --samples TEXT        comma separated list of samples to process

      Receipt Options:
        --no-overlap  skip per lineage overlap column

      General Options:
        -v, --verbose                  show more output, set log level to debug
        -c, --config FILE              read parameter values from config file [default: pycashier.toml]
        --save-config [explicit|full]  save current params to file specified by `--config`
        --log-file FILE                path to log file [default: <pipeline-dir>/pycashier.log] 
        -h, --help                     Show this message and exit.



pycashier scrna
----------------------------------


.. tab:: image

  .. image:: svgs/pycashier-scrna.svg

.. tab:: plaintext

  .. code-block::

      Usage: pycashier scrna [OPTIONS]

        extract expressed DNA barcodes from scRNA-seq

        Designed for interoperability with 10X scRNA-seq workflow.
        After processing samples with `cellranger` resulting
        bam files should be converted to sam files using `samtools`.

        NOTE: You can speed this up by providing a sam file with only the unmapped reads.

      Input/Output Options:
        -i, --input DIRECTORY     source directory containing sam files from scRNA-seq [required]
        -o, --output DIRECTORY    output directory [default: ./outs]
        -p, --pipeline DIRECTORY  pipeline directory [default: ./pipeline]
        -s, --samples TEXT        comma separated list of samples to process

      Trim (Cutadapt) Options:
        -e, --error FLOAT               error tolerance supplied to cutadapt [default: 0.1]
        -l, --length INTEGER            target length of extracted barcode [default: 20]
        -ua, --upstream-adapter TEXT    5' sequence flanking barcode
        -da, --downstream-adapter TEXT  3' sequence flanking barcode
        -ca, --cutadapt-args TEXT       additional arguments passed to cutadapt [default: --max-n=0 -n 2
                                        --trimmed-only]
        -ml, --minimum-length INTEGER   minimum length of extracted barcode [default: 10]

      General Options:
        -t, --threads INTEGER          number of cpu cores to use [default: 1]
        -y, --yes                      answer yes to prompts
        -v, --verbose                  show more output, set log level to debug
        -c, --config FILE              read parameter values from config file [default: pycashier.toml]
        --save-config [explicit|full]  save current params to file specified by `--config`
        --log-file FILE                path to log file [default: <pipeline-dir>/pycashier.log] 
        -h, --help                     Show this message and exit.

