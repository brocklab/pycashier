import os
import re
from pathlib import Path

from .cli import get_args
from .cluster import cluster
from .extract import extract
from .merge import merge
from .read_filter import read_filter
from .single_cell import single_cell


def main():

    cli_args = get_args()

    sourcedir = Path(cli_args['main']['sourcedir'])

    fastqs = [f for f in sourcedir.iterdir()]

    Path('pipeline').mkdir(exist_ok=True)
    Path('outs').mkdir(exist_ok=True)

    if cli_args['single_cell']:

        single_cell(sourcedir, cli_args)

    if cli_args['merge']['merge']:

        merge(fastqs, sourcedir, cli_args)

    for f in fastqs:

        ext = f.suffix
        
        if ext != '.fastq':
            print(
                'ERROR! There is a non fastq file in the provided fastq directory: {}'
                .format(f))
            print('Exiting.')
            exit()

    #for child in sourcedir.iterdir(): print(child)
    print(
        'performing barcode extraction and clustering for {} samples\n'.format(
            len(fastqs)))

    for fastq in fastqs:

        #fastq should be file name of the fastqs.

        sample = fastq.name.split('.')[0]

        extract(sample, fastq, **cli_args['main'], **cli_args['extract'])

        cluster(sample, **cli_args['main'], **cli_args['cluster'])

        read_filter(sample, **cli_args['main'], **cli_args['filter'],
                    **cli_args['cluster'])

        print('completed processsing for sample: {}\n\n'.format(sample))


if __name__ == '__main__':
    main()
