import shlex
import subprocess
from pathlib import Path

from .utils import extract_csv_column


def cluster(sample, ratio, distance, quality, threads, **kwargs):
    pipeline = Path('pipeline')

    extracted_csv = pipeline / f'{sample}.barcodes.q{quality}.tsv'

    input_file = extract_csv_column(extracted_csv, 2)

    output_file = pipeline / '{}.barcodes.q{}.r{}d{}.tsv'.format(
        sample, quality, ratio, distance)

    if not output_file.is_file():

        command = 'starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {output_file}'.format(
            distance=distance,
            ratio=ratio,
            threads=threads,
            input_file=input_file,
            output_file=output_file)

        args = shlex.split(command)

        p = subprocess.run(args)

        print('clustering complete\n\n')
    else:
        print('Found clustered reads for sample: {}\n'.format(sample))

    print('clustering for {} complete'.format(sample))
