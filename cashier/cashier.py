import re
from pathlib import Path

from .cli import console, get_args, sample_check
from .cluster import cluster
from .extract import extract
from .merge import merge
from .read_filter import read_filter
from .single_cell import single_cell


def main():

    cli_args = get_args()

    sourcedir = Path(cli_args['main']['sourcedir'])

    fastqs = [f for f in sourcedir.iterdir()]

    if cli_args['single_cell']:

        single_cell(sourcedir, cli_args)

    if cli_args['merge']['merge']:

        merge(fastqs, sourcedir, cli_args)

    for f in fastqs:

        ext = f.suffix

        if ext != '.fastq':
            print(
                f'ERROR! There is a non fastq file in the provided fastq directory: {f}'
            )
            print('Exiting.')
            exit()

    Path('pipeline').mkdir(exist_ok=True)
    Path('outs').mkdir(exist_ok=True)

    sample_check(sourcedir, fastqs, cli_args)

    for fastq in fastqs:

        sample = fastq.name.split('.')[0]

        with console.status(f"Processing sample: {sample}",spinner='bouncingBall'):

            extract(sample, fastq, **cli_args['main'], **cli_args['extract'])

            cluster(sample, **cli_args['main'], **cli_args['cluster'])

            read_filter(sample, **cli_args['main'], **cli_args['filter'],
                        **cli_args['cluster'])

        # print(f'completed processsing for sample: {sample}\n\n')
        console.log(f'Procressing for {sample} has completed')
    
    print('\nfinished')

if __name__ == '__main__':
    main()
