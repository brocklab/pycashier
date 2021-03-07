import os
import shlex
import subprocess
from pathlib import Path

from .utils import fastq_to_csv


def extract(sample, fastq, sourcedir, error_rate, threads, barcode_length,
            upstream_adapter, downstream_adapter, unlinked_adapters, quality,
            **kwargs):

    pipeline = Path('pipeline')
    barcode_fastq = pipeline / f'{sample}.barcode.fastq'
    input_file = fastq
    filtered_barcode_fastq = pipeline / f'{sample}.barcode.q{quality}.fastq'

    if unlinked_adapters:
        adapter_string = '-g {} -a {}'.format(upstream_adapter,
                                              downstream_adapter)
    else:
        adapter_string = '-g {}...{}'.format(upstream_adapter,
                                             downstream_adapter)

    if not filtered_barcode_fastq.is_file():

        print('performing extraction on sample: {}'.format(sample))

        command = 'cutadapt -e {error_rate} -j {threads} --minimum-length={barcode_length} --maximum-length={barcode_length} --max-n=0 --trimmed-only {adapter_string} -n 2 -o {barcode_fastq} {input_file}'.format(
            error_rate=error_rate,
            threads=threads,
            barcode_length=barcode_length,
            adapter_string=adapter_string,
            barcode_fastq=barcode_fastq,
            input_file=input_file)
        args = shlex.split(command)

        p = subprocess.run(args)

        command = 'fastq_quality_filter -q {quality} -p 100 -i {barcode_fastq} -o {filtered_barcode_fastq} -Q 33'.format(
            quality=quality,
            barcode_fastq=barcode_fastq,
            filtered_barcode_fastq=filtered_barcode_fastq)

        args = shlex.split(command)

        p = subprocess.run(args)

        barcode_fastq.unlink()

    else:
        print('using extracted barcode fastq from pipeline for sample: {}'.
              format(sample))

    barcodes_out = pipeline / f'{sample}.barcodes.q{quality}.tsv'

    if not barcodes_out.is_file():
        fastq_to_csv(filtered_barcode_fastq, barcodes_out)
    else:
        print(
            'using extracted  barcode tsv from pipeline for sample: {}'.format(
                sample))

    print('extraction complete!')
