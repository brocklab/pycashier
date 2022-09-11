import re
import sys

from .term import term
from .utils import check_output, confirm_samples, run_cmd


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
                    f"[MergeError]: detected multiple [hl]{read}[/] files for [hl]{sample}[/]\n"
                    f"files: [b]{f}[/] and [b]{pefastqs[sample][read]}[/]",
                    err=True,
                )
                sys.exit(1)

        else:
            term.print(
                f"[MergeError]: failed to obtain sample/read info from [b]{f}[/]\n",
                "Merge mode expects fastq(.gz) files with R1 or R2 in the name. Exiting.",
                err=True,
            )
            sys.exit(1)

    return pefastqs


def merge_single(
    sample, pefastqs, pipeline, output, threads, verbose, fastp_args, status
):

    merged_barcode_fastq = output / f"{sample}.merged.raw.fastq"

    if check_output(merged_barcode_fastq, "merging paired end reads w/ [b]fastp[/]"):

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


def merge_all(fastqs, input, pipeline, output, threads, verbose, fastp_args, yes):
    for d in [pipeline, output]:
        d.mkdir(exist_ok=True)

    pefastqs = get_pefastqs(fastqs)

    confirm_samples(pefastqs.keys(), yes)

    for sample in sorted(pefastqs):
        term.process(f"[hl]{sample}[/]", status="start")

        with term.cash_in() as status:
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

        term.process("fastqs sucessfully merged")
        term.process(status="end")

    term.print("\n[green]FINISHED!")
    sys.exit()
