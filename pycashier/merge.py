import re
import sys

from .term import term
from .utils import run_cmd

# TODO: make a file collextion to generate a dict wtih two files for each sample


def get_pefastqs(fastqs):

    pefastqs = {}

    for f in fastqs:

        m = re.search(r"(?P<sample>.+?)\..*(?P<read>R[1-2])\..*\.fastq.*", f.name)
        if m:
            sample, read = m.groups()
            pefastqs.setdefault(sample, {})

            if read not in pefastqs[sample]:
                pefastqs[sample][read] = f
            else:
                term.print(
                    f"[MergeError]: detected multiple [hl]{read}[/] files for [hl]{sample}[/]",
                    err=True,
                )
                term.print(f"files: [b]{f}[/] and [b]{pefastqs[sample][read]}[/]")
                sys.exit(1)
        else:
            term.print(
                f"[MergeError]: failed to obtain sample/read info from [b]{f}[/]",
                err=True,
            )
            term.print(
                "Merge mode expects fastq(.gz) files with R1 or R2 in the name. Exiting."
            )
            sys.exit(1)

    return pefastqs


def merge_single(
    sample, pefastqs, pipeline, output, threads, verbose, fastp_args, status
):

    merged_barcode_fastq = output / f"{sample}.merged.raw.fastq"

    if not merged_barcode_fastq.is_file():

        term.print(f"[green]{sample}[/green]: starting fastq merge")
        command = (
            "fastp "
            f"-i {pefastqs['R1']}  "
            f"-I {pefastqs['R2']}  "
            f"-w {threads} "
            "-m -c -G -Q -L "
            f"-j {pipeline}/merge_qc/{sample}.json "
            f"-h {pipeline}/merge_qc/{sample}.html "
            f"--merged_out {merged_barcode_fastq} "
            f"{fastp_args or ''}"
        )

        run_cmd(command, sample, merged_barcode_fastq, verbose, status)

    else:
        term.print(f"[green]{sample}[/green]: Found merged barcode fastq")
        term.print(f"[green]{sample}[/green]: skipping fastq merge")


def merge_all(fastqs, input, pipeline, output, threads, verbose, fastp_args, yes):
    for d in [pipeline, output]:
        d.mkdir(exist_ok=True)

    pefastqs = get_pefastqs(fastqs)

    term.print(f"[hl]Samples[/]: {', '.join(sorted(pefastqs))}\n")

    if not yes and not term.confirm("Continue with these samples?"):
        sys.exit()

    for sample in sorted(pefastqs):
        term.print(f"\n──────────────── {sample} ───────────────────", style="dim")

        with term.status(
            f"Processing sample: [green]{sample}[/green]", spinner="dots2"
        ) as status:

            merge_single(
                sample,
                pefastqs[sample],
                pipeline,
                output,
                threads,
                verbose,
                fastp_args,
                status,
            )

        term.print(f"[green]{sample}[/green]: processing completed")

    term.print("\n[green]FINISHED!")
    sys.exit()
