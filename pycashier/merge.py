import re
import shlex
import subprocess
import sys
from pathlib import Path

from .console import console


def merge_single(
    sample, fastqs, sourcedir, threads, verbose, pipelinedir, pear_args, keep_output
):
    pipeline = Path(pipelinedir)

    # TODO: refactor for clarity and memory usage
    for f in fastqs:

        R1_regex = r"" + re.escape(sample) + r"\..*R1.*\.fastq\.gz"
        m = re.search(R1_regex, f.name)
        if m:
            R1_file = m.group(0)

        R2_regex = r"" + re.escape(sample) + r"\..*R2.*\.fastq\.gz"
        m = re.search(R2_regex, f.name)
        if m:
            R2_file = m.group(0)

    if R1_file is None or R2_file is None:
        print("oops I didnt find an R1 or R2 file")
        sys.exit(1)

    mergedfastq = Path("mergedfastqs")
    merged_barcode_fastq = mergedfastq / f"{sample}.merged.raw.fastq"
    merged_barcode_file_prefix = pipeline / f"{sample}.merged.raw"

    files = [R1_file, R2_file]

    if not merged_barcode_fastq.is_file():

        console.log(f"[green]{sample}[/green]: extracting and moving fastqs")
        # future implementations may use a python based extraction (using gzip)
        # TODO: Make fastq extraction conditional

        path_to_r1 = sourcedir / R1_file
        path_to_r2 = sourcedir / R2_file

        command = f"gunzip -k {path_to_r1} {path_to_r2}"
        args = shlex.split(command)
        p = subprocess.run(args)

        files = [Path(f) for f in files]  # replace with sample dict of files

        for f in files:

            old_path = sourcedir / f.stem
            new_path = pipeline / f.stem
            old_path.rename(new_path)

        console.log(f"[green]{sample}[/green]: starting fastq merge")
        command = f"pear -f {path_to_r1} -r {path_to_r2} \
            -o {merged_barcode_file_prefix} -j {threads} {pear_args}"
        args = shlex.split(command)

        p = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        if verbose:
            console.print("[yellow]PEAR OUTPUT:")
            console.print(p.stdout)

        # remove the extra files made from pear
        if not keep_output:
            for suffix in [
                "discarded.fastq",
                "unassembled.forward.fastq",
                "unassembled.reverse.fastq",
            ]:
                f = Path(f"{merged_barcode_file_prefix}.{suffix}")
                f.unlink()

        merged_barcode_file_prefix.with_suffix(
            merged_barcode_file_prefix.suffix + ".assembled.fastq"
        ).rename(merged_barcode_fastq)

    else:
        print(f"Found merged barcode fastq for sample:{sample}")
        console.log(f"[green]{sample}[/green]: skipping fastq merge")


def merge(fastqs, sourcedir, cli_args):
    console.rule("MERGE MODE", align="center", style="red")
    print()
    Path("mergedfastqs").mkdir(exist_ok=True)

    samples = []

    for f in fastqs:

        m = re.search(r"(.+?)\..*R.*\.fastq\.gz", f.name)
        if m:
            samples.append(m.group(1))
        else:
            print(f"Failed to obtain sample name from {f}")
            sys.exit(1)

    print("Found the following samples:")
    for s in set(samples):
        console.print(f"[green]{s}")
    print()

    if len(samples) / len(set(samples)) != 2:
        print("There should be an R1 and R2 fastq file for each sample.")
        sys.exit(1)

    for sample in set(samples):

        with console.status(
            f"Processing sample: [green]{sample}[/green]", spinner="dots12"
        ):

            merge_single(
                sample,
                fastqs,
                sourcedir,
                cli_args["main"]["threads"],
                verbose=cli_args["main"]["verbose"],
                pipelinedir=cli_args["main"]["pipelinedir"],
                pear_args=cli_args["merge"]["pear_args"],
                keep_output=cli_args["merge"]["keep_output"],
            )

        console.log(f"[green]{sample}[/green]: processing completed")
        console.rule()

    console.print("\n[green]FINISHED!")
    sys.exit()
