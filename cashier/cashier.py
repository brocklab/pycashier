#!/usr/bin/env python3
import os
import re

from .cli import get_args
from .extract import extract
from .cluster import cluster
from .merge import merge


def main():
    """
    doc string 
    """
    
    cli_args=get_args()

    fastqdir = cli_args['main']['fastqdir']

    #fastq file check 
    fastqs = os.listdir(fastqdir)

    if cli_args['merge']['merge']:
        
        merge(fastqs, fastqdir, cli_args)

    for f in fastqs:
        ext = os.path.splitext(f)[-1].lower()
        if ext != '.fastq':
            print('ERROR! There is a non fastq file in the provided fastq directory: {}'.format(f))
            print('Exiting.')
            exit()

    if not os.path.exists('pipeline'):
        os.makedirs('pipeline')
    if not os.path.exists('outs'):
        os.makedirs('outs')

    os.chdir('pipeline')

    print('Performing extraction and clustering for {} samples'.format(len(fastqs)))

    for fastq in fastqs: 

        #fastq should be file name of the fastqs.

        sample = os.path.basename(os.path.join(fastqdir,fastq)).split('.')[0]

        extract(sample,fastq,**cli_args['main'],**cli_args['extract'])
    
        cluster(sample,**cli_args['main'],**cli_args['cluster'])

if __name__ == '__main__':
    main()
