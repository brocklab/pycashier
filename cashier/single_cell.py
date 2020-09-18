import sys 
import os 
import shlex
import subprocess

from .utils import sam_to_name_labeled_fastq, labeled_fastq_to_tsv

def single_cell_process(sample,f,sourcedir,cli_args):
    print('performing barcode extraction on sample: {}'.format(sample))


    error_rate = cli_args['extract']['error_rate']
    threads = cli_args['main']['threads']
    barcode_length = cli_args['extract']['barcode_length']
    upstream_adapter = cli_args['extract']['upstream_adapter']
    downstream_adapter = cli_args['extract']['downstream_adapter']
    adapter_string = '-g {} -a {}'.format(upstream_adapter,downstream_adapter)

    input_file = os.path.join('../',sourcedir,f)
    fastq_out = "{}.cell_record_labeled.fastq".format(sample)
    output_file = "{}.cell_record_labeled.barcode.fastq".format(sample)
    tsv_out = '{}.cell_record_labeled.barcode.tsv'.format(sample)

    if not os.path.isfile(fastq_out):
        sam_to_name_labeled_fastq(input_file, fastq_out)
    else:
        print("using the fastq found in pipeline directory")
    
    if not os.path.isfile(output_file):
        
        print('Performing extraction on sample: {}'.format(sample))
    
        command = 'cutadapt -e {error_rate} -j {threads} --minimum-length={barcode_length_min} --maximum-length={barcode_length} --max-n=0 --trimmed-only {adapter_string} -n 2 -o {output_file} {input_file}'.format(
            error_rate = error_rate,
            threads = threads,
            barcode_length_min = 10,
            barcode_length = barcode_length,
            adapter_string = adapter_string,
            output_file = output_file,
            input_file = fastq_out
        )
        args = shlex.split(command)

        p = subprocess.run(args)

    
    if not os.path.isfile(tsv_out):
        labeled_fastq_to_tsv(output_file,tsv_out)
    else:
        print('Found an extracted and record labeled barcode tsv for sample: {}'.format(sample))
    
    print('Completed barcode extraction for sample: {}'.format(sample))
    

def single_cell(sourcedir, cli_args):

    sam_files = []

    for f in os.listdir(sourcedir):
        
        ext = os.path.splitext(f)[-1].lower()

        if ext != '.sam':
            print('ERROR! There is a non sam file in the provided input directory: {}'.format(f))
            print('Please convert all bam files using samtools view first')
            print('Exiting.')
            exit()

        sam_files.append(f)
    
    os.chdir('pipeline')
    
    for f in sam_files:

        sample = os.path.basename(os.path.join(sourcedir,f)).split('.')[0]
    
        single_cell_process(sample,f,sourcedir,cli_args)
 
    print('\nfinished extracting barcodes from sam files')
    print('exiting.')
    exit()
    
    

