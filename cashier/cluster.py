import os
import shlex
import subprocess

from .utils import extract_csv_column


def cluster(sample,ratio,distance,quality,threads,**kwargs):
    
    extracted_csv = '{}.barcodes.q{}.tsv'.format(sample,quality)

    input_file = extract_csv_column(extracted_csv,2)

    output_file = '{}.barcodes.q{}.r{}d{}.tsv'.format(sample,quality,ratio,distance)
    
    if not os.path.isfile(output_file):
    
        command = 'starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {output_file}'.format(
            distance=distance,
            ratio=ratio,
            threads=threads,
            input_file=input_file,
            output_file=output_file
        )

        args = shlex.split(command)

        p = subprocess.run(args)
    
        print('clustering complete\n\n')
    else:
        print('Found clustered reads for sample: {}\n'.format(sample))

    print('clustering for {} complete'.format(sample))
