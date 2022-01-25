import re
import shlex
import subprocess
import sys
from pathlib import Path

from rich.prompt import Confirm

from .console import console


def merge_single(
    sample,
    fastqs,
    sourcedir,
    threads,
    verbose,
    pipelinedir,
    fastp_args,
):
    pipeline = Path(pipelinedir)
    (pipeline / "merge_qc").mkdir(exist_ok=True)

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

    if not merged_barcode_fastq.is_file():

        console.log(f"[green]{sample}[/green]: extracting and moving fastqs")
        # future implementations may use a python based extraction (using gzip)
        # TODO: Make fastq extraction conditional

        path_to_r1 = sourcedir / R1_file
        path_to_r2 = sourcedir / R2_file

        console.log(f"[green]{sample}[/green]: starting fastq merge")
        command = f"fastp \
                -i {path_to_r1}  \
                -I {path_to_r2} \
                -w {threads} \
                -m -c -G -Q -L \
                -j {pipeline}/merge_qc/{sample}.json \
                -h {pipeline}/merge_qc/{sample}.html \
                --merged_out {merged_barcode_fastq} \
                {fastp_args}"

        args = shlex.split(command)

        p = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        if verbose:
            console.print("[yellow]FASTP OUTPUT:")
            console.print(p.stdout)

    else:
        console.log(f"[green]{sample}[/green]: Found merged barcode fastq")
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
            print("Merge mode expects gzipped fastqs. Exiting.")
            sys.exit(1)

    print("Found the following samples:")
    for s in set(samples):
        console.print(f"[green]{s}")
    print()
    if not Confirm.ask("Continue with these samples?"):
        sys.exit()

    if len(samples) / len(set(samples)) != 2:
        print("There should be an R1 and R2 fastq file for each sample.")
        sys.exit(1)

    for sample in sorted(set(samples)):

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
                fastp_args=cli_args["merge"]["fastp_args"],
            )

        console.log(f"[green]{sample}[/green]: processing completed")
        console.rule()

    console.print("\n[green]FINISHED!")
    sys.exit()
