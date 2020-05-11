#!/usr/bin/env python3
import os

from .cli import get_args
from .extract import extract
from .cluster import cluster





def main():
    """
    doc string goes here 
    """
    
    cli_args=get_args()

    fastqdir = cli_args['main']['fastqdir']

    if not os.path.exists('pipeline'):
        os.makedirs('pipeline')
    if not os.path.exists('outs'):
        os.makedirs('outs')
    fastqs = os.listdir(fastqdir)

    for f in fastqs:
        ext = os.path.splitext(f)[-1].lower()
        if ext != '.fastq':
            print('There is a non fastq file in the provided fastq directory: {}'.format(f))
            print('exiting now')
            exit()
             


    print('Performing extraction and clustering for {} samples'.format(len(fastqs)))

    
    os.chdir('pipeline')

    for fastq in fastqs: 
        #path/to/fastqs
        #fastq should be file name of the fastqs.
        sample = os.path.basename(os.path.join(fastqdir,fastq)).split('.')[0]
        
        extract(sample,fastq,**cli_args['main'],**cli_args['extract'])
    
        cluster(sample,**cli_args['main'],**cli_args['cluster'])

        
    #remove based on minimum? 


if __name__ == '__main__':
    main()
