import os
import subprocess
import shlex

from .utils import extract_csv_column, post_clustering_min


def cluster(sample,ratio,distance,quality,threads,filter_count,**kwargs):
    filter
    
    extracted_csv = '{}.barcodes.q{}.tsv'.format(sample,quality)

    input_file = extract_csv_column(extracted_csv,2)
    #input_file = 'tmp100.c2.tsv'
    output_file = '{}.barcodes.r{}d{}.tsv'.format(sample,ratio,distance)
    if not os.path.isfile(output_file):
    
        command = 'starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {output_file}'.format(
            distance=distance,
            ratio=ratio,
            threads=threads,
            input_file=input_file,
            output_file=output_file
        )

        args = shlex.split(command)

        p = subprocess.Popen(args)
        p.wait()
    
        print('clustering complete\n\n')
    else:
        print('Found clustered reads form sample: {}\n'.format(sample))

    post_clustering_min(output_file,filter_count)

    print('Processing for {} complete!'.format(sample))

    
