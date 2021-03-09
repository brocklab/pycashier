import sys
import shlex
import subprocess
from pathlib import Path

from .utils import sam_to_name_labeled_fastq, labeled_fastq_to_tsv


def single_cell_process(sample, f, sourcedir, cli_args):
    print(f'performing barcode extraction on sample: {sample}')

    error_rate = cli_args['extract']['error_rate']
    threads = cli_args['main']['threads']
    barcode_length = cli_args['extract']['barcode_length']
    upstream_adapter = cli_args['extract']['upstream_adapter']
    downstream_adapter = cli_args['extract']['downstream_adapter']
    adapter_string = f'-g {upstream_adapter} -a {downstream_adapter}'

    input_file = f
    pipeline_dir = Path('pipeline')
    fastq_out = pipeline_dir / f"{sample}.cell_record_labeled.fastq"
    output_file = pipeline_dir / f"{sample}.cell_record_labeled.barcode.fastq"
    tsv_out = Path('outs') / f'{sample}.cell_record_labeled.barcode.tsv'

    if not fastq_out.is_file():
        sam_to_name_labeled_fastq(input_file, fastq_out)
    else:
        print("using the fastq found in pipeline directory")

    if not output_file.is_file():

        print(f'Performing extraction on sample: {sample}')

        command = f'cutadapt -e {error_rate} -j {threads} --minimum-length={barcode_length_min} --maximum-length={barcode_length} --max-n=0 --trimmed-only {adapter_string} -n 2 -o {output_file} {input_file}'
        args = shlex.split(command)

        p = subprocess.run(args)

    if not tsv_out.is_file():
        labeled_fastq_to_tsv(output_file, tsv_out)
    else:
        print(
            f'Found an extracted and record labeled barcode tsv for sample: {sample}'
        )

    print(f'Completed barcode extraction for sample: {sample}')


def single_cell(sourcedir, cli_args):

    sam_files = [f for f in sourcedir.iterdir()]

    for f in sam_files:

        ext = f.suffix

        if ext != '.sam':
            print(
                f'ERROR! There is a non sam file in the provided input directory: {f}'
            )
            print('Please convert all bam files using samtools view first')
            print('Exiting.')
            exit()

    for f in sam_files:

        sample = f.name.split('.')[0]

        single_cell_process(sample, f, sourcedir, cli_args)

    print('\nfinished extracting barcodes from sam files')
    print('exiting.')
    exit()
