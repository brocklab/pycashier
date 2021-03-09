import re
import shlex
import subprocess
from pathlib import Path


def merge_single(sample, fastqs, sourcedir, threads, **kwargs):
    keep_output = kwargs['keep_output']
    pear_args = kwargs['pear_args']

    print(f"Beginning work with sample: {sample}")

    for f in fastqs:

        R1_regex = r"" + re.escape(sample) + "\..*R1.*\.fastq\.gz"
        m = re.search(R1_regex, f.name)
        if m:
            R1_file = m.group(0)

        R2_regex = r"" + re.escape(sample) + "\..*R2.*\.fastq\.gz"
        m = re.search(R2_regex, f.name)
        if m:
            R2_file = m.group(0)

    if R1_file == None or R2_file == None:
        print("oops I didnt find an R1 or R2 file")
        exit()
    mergedfastq = Path('mergedfastqs')
    merged_barcode_fastq = mergedfastq / f'{sample}.merged.raw.fastq'
    merged_barcode_file_prefix = Path('pipeline') / Path(
        f'{sample}.merged.raw')
    #! what happens if i specify the prefix with a path?

    files = [R1_file, R2_file]

    if not merged_barcode_fastq.is_file():

        print(f'Performing fastq merge on sample: {sample}\n')
        #future implementations may use a python based extraction (using gzip)

        print('Extracting and moving fastqs')

        path_to_r1 = sourcedir / R1_file
        path_to_r2 = sourcedir / R2_file

        command = f"gunzip -k {path_to_r1} {path_to_r2}"
        args = shlex.split(command)
        p = subprocess.run(args)

        files = [Path(f) for f in files]  # replace with sample dict of files

        for f in files:

            old_path = sourcedir / f.stem
            new_path = Path('pipeline') / f.stem
            old_path.rename(new_path)

        print('Merging fastqs')

        command = f'pear -f {path_to_r1} -r {path_to_r2} -o {merged_barcode_file_prefix} -j {threads} {pear_args}'
        args = shlex.split(command)
        p = subprocess.run(args)

        #remove the extra files made from pear
        if not kwargs['keep_output']:
            for suffix in [
                    'discarded.fastq', 'unassembled.forward.fastq',
                    'unassembled.reverse.fastq'
            ]:
                file = Path(f'{merged_barcode_file_prefix}.{suffix}')
                file.unlink(file)

        merged_barcode_file_prefix.with_suffix(
            merged_barcode_file_prefix.suffix +
            '.assembled.fastq').rename(merged_barcode_fastq)

    else:
        print(f'Found merged barcode fastq for sample:{sampl}')


def merge(fastqs, sourcedir, cli_args):

    Path('mergedfastqs').mkdir(exist_ok=True)

    samples = []

    for f in fastqs:

        m = re.search(r'(.+?)\..*R.*\.fastq\.gz', f.name)
        if m:
            samples.append(m.group(1))
        else:
            #TODO: make value error?
            print(f'Failed to obtain sample name from {f}')
            exit()

    print('Found the following samples:')
    for s in set(samples):
        print(s)
    print()

    if len(samples) / len(set(samples)) != 2:
        print("There should be an R1 and R2 fastq file for each sample.")
        exit()

    for sample in set(samples):

        merge_single(sample, fastqs, sourcedir, cli_args['main']['threads'],
                     **cli_args['merge'])

    print("\nCleaning up single read fastq files.")

    print("All samples have been merged and can be found in mergedfastqs\n")
    exit()
