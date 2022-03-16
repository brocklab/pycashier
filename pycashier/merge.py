import re
import shlex
import subprocess
import sys

from rich.prompt import Confirm

from .console import console


def merge_single(sample, fastqs, input, pipeline, output, threads, verbose, fastp_args):
    (pipeline / "merge_qc").mkdir(exist_ok=True)

    # TODO: refactor for clarity and memory usage
    # also allow unzipped fastqs
    for f in fastqs:

        R1_regex = r"" + re.escape(sample) + r"\..*R1.*\.fastq.*"  # \.gz"
        m = re.search(R1_regex, f.name)
        if m:
            R1_file = m.group(0)

        R2_regex = r"" + re.escape(sample) + r"\..*R2.*\.fastq.*"  # \.gz"
        m = re.search(R2_regex, f.name)
        if m:
            R2_file = m.group(0)

    if R1_file is None or R2_file is None:
        print("oops I didn't find an R1 or R2 file")
        sys.exit(1)

    merged_barcode_fastq = output / f"{sample}.merged.raw.fastq"

    if not merged_barcode_fastq.is_file():

        path_to_r1 = input / R1_file
        path_to_r2 = input / R2_file

        console.print(f"[green]{sample}[/green]: starting fastq merge")
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

        if p.returncode != 0 or merged_barcode_fastq.stat().st_size == 0:
            console.print("[red]FASTP FAILED!")
            console.print("[yellow]FASTP OUTPUT:")
            console.print(p.stdout)
            sys.exit()

        if verbose:
            console.print("[yellow]FASTP OUTPUT:")
            console.print(p.stdout)

    else:
        console.print(f"[green]{sample}[/green]: Found merged barcode fastq")
        console.print(f"[green]{sample}[/green]: skipping fastq merge")


def merge_all(fastqs, input, pipeline, output, threads, verbose, fastp_args):
    for d in [pipeline, output]:
        d.mkdir(exist_ok=True)

    samples = []

    for f in fastqs:

        m = re.search(r"(.+?)\..*R.*\.fastq.*", f.name)
        if m:
            samples.append(m.group(1))
        else:
            print(f"Failed to obtain sample name from {f}")
            print("Merge mode expects gzipped fastqs. Exiting.")
            sys.exit(1)

    console.print(f"[b cyan]Samples[/]: {', '.join(sorted(set(samples)))}\n")

    if not Confirm.ask("Continue with these samples?"):
        sys.exit()

    if len(samples) / len(set(samples)) != 2:
        print("There should be an R1 and R2 fastq file for each sample.")
        sys.exit(1)

    for sample in sorted(set(samples)):

        print()
        console.print(f"──────────────── {sample} ───────────────────", style="dim")

        with console.status(
            f"Processing sample: [green]{sample}[/green]", spinner="dots12"
        ):

            merge_single(
                sample, fastqs, input, pipeline, output, threads, verbose, fastp_args
            )

        console.print(f"[green]{sample}[/green]: processing completed")

    console.print("\n[green]FINISHED!")
    sys.exit()
