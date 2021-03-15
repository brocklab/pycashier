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
        adapter_string = f'-g {upstream_adapter} -a {downstream_adapter}'
    else:
        adapter_string = f'-g {upstream_adapter}...{downstream_adapter}'

    if not filtered_barcode_fastq.is_file():

        print(f'performing extraction on sample: {sample}')

        command = f'cutadapt -e {error_rate} -j {threads} --minimum-length={barcode_length} --maximum-length={barcode_length} --max-n=0 --trimmed-only {adapter_string} -n 2 -o {barcode_fastq} {input_file}'
        args = shlex.split(command)

        p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

        if kwargs['verbose']:
            print(p.stdout)
        
        command = f'fastq_quality_filter -q {quality} -p 100 -i {barcode_fastq} -o {filtered_barcode_fastq} -Q 33'

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
            f'using extracted  barcode tsv from pipeline for sample: {sample}')

    print('extraction complete!')
