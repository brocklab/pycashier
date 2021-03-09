import shlex
import subprocess
from pathlib import Path

from .utils import extract_csv_column


def cluster(sample, ratio, distance, quality, threads, **kwargs):
    pipeline = Path('pipeline')

    extracted_csv = pipeline / f'{sample}.barcodes.q{quality}.tsv'

    input_file = extract_csv_column(extracted_csv, 2)

    output_file = pipeline / f'{sample}.barcodes.q{quality}.r{ratio}d{distance}.tsv'

    if not output_file.is_file():

        command = f'starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {output_file}'

        args = shlex.split(command)

        p = subprocess.run(args)

        print('clustering complete\n\n')
    else:
        print(f'Found clustered reads for sample: {sample}\n')

    print(f'clustering for {sample} complete')
