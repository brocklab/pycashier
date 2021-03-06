import os
import re

from .cli import get_args
from .extract import extract
from .cluster import cluster
from .merge import merge
from .read_filter import read_filter
from .single_cell import single_cell

def main():

    cli_args=get_args()

    sourcedir = cli_args['main']['sourcedir']

    fastqs = os.listdir(sourcedir)

    if not os.path.exists('pipeline'):
        os.makedirs('pipeline')
    if not os.path.exists('outs'):
        os.makedirs('outs')

    if cli_args['single_cell']:

        single_cell(sourcedir,cli_args)

    if cli_args['merge']['merge']:
    
        merge(fastqs, sourcedir, cli_args)

    for f in fastqs:
        ext = os.path.splitext(f)[-1].lower()
        if ext != '.fastq':
            print('ERROR! There is a non fastq file in the provided fastq directory: {}'.format(f))
            print('Exiting.')
            exit()

    os.chdir('pipeline')

    print('performing barcode extraction and clustering for {} samples\n'.format(len(fastqs)))

    for fastq in fastqs: 

        #fastq should be file name of the fastqs.

        sample = os.path.basename(os.path.join(sourcedir,fastq)).split('.')[0]

        extract(sample,fastq,**cli_args['main'],**cli_args['extract'])
    
        cluster(sample,**cli_args['main'],**cli_args['cluster'])

        read_filter(sample,**cli_args['main'],**cli_args['filter'],**cli_args['cluster'])

        print('completed processsing for sample: {}\n\n'.format(sample))

if __name__ == '__main__':
    main()
