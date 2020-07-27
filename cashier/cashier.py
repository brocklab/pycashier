#!/usr/bin/env python3
import os
import re

from .cli import get_args
from .extract import extract
from .cluster import cluster
from .merge import merge


def main():
    """
    doc string goes here 
    """
    
    cli_args=get_args()

    fastqdir = cli_args['main']['fastqdir']


    #fastq file check 
    fastqs = os.listdir(fastqdir)


    if cli_args['main']['merge']:

        if not os.path.exists('mergedfastqs'):
            os.makedirs('mergedfastqs')


        samples=[]
        
        for f in fastqs:

            m=re.search(r'(.+?)\..*R.*\.fastq\.gz',f)
            if m:
                samples.append(m.group(1))
            else:
                print('Failed to obtain sample name from {}'.format(f))
                exit()

        print('Found the following samples:')
        for s in set(samples): print(s)
        print()

        if len(samples)/len(set(samples))!=2:
            print("There should be an R1 and R2 fastq file for each sample.")
            exit()

        os.chdir('mergedfastqs')

        for sample in set(samples):
            
            merge(sample,fastqs,fastqdir)

        print("\nCleaning up single read fastq files.")

        clean_fastqs = os.listdir('.')
        for f in clean_fastqs:
            if "R1" in f or "R2" in f:
                os.remove(f)

        print("All samples have been merged and can be found in mergedfastqs\n")
        exit()
    


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

        #add a seperate filtering method here based on percent of count filter


if __name__ == '__main__':
    main()
