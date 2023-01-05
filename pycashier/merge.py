import re
import sys
from pathlib import Path
from typing import Dict, List

from rich.status import Status

from .term import term
from .utils import check_output, confirm_samples, run_cmd


def get_pefastqs(fastqs: List[Path]) -> Dict[str, Dict[str, Path]]:
    """parse input files for paired-end sequences

    Args:
        fastqs: list of fastq files from input directory
    Returns:
        dictionary of sample and paired-end fastq files
    """
    pefastqs: Dict[str, Dict[str, Path]] = {}
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

    for sample, reads in pefastqs.items():
        if len(reads) != 2:
            term.print(
                "[MergeError]: please ensure there is and R1 and R2 for all samples"
            )
            term.print("[MergeError]: detected the following samples")
            term.print(pefastqs)
            sys.exit(1)

    return pefastqs


def merge_single(
    sample: str,
    pefastqs: Dict[str, Path],
    pipeline: Path,
    output: Path,
    threads: int,
    verbose: bool,
    fastp_args: Dict[str, str],
    status: Status,
) -> None:
    """merge a single sample with fastp

    Args:
        sample: Name of the sample.
        pefasts: Dictionary of paired-end reads and paths.
        pipeline: Directory for all intermediary files.
        output: Directory for final merged fastq files.
        threads: Number of threads for starcode to use.
        verbose: If true, show subcommand output.
        fastp_args: Extra arguments passed to fastp.
        status: Rich.console status to suspend for stderr printing.

    """

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
        term.process("fastqs sucessfully merged")


def merge_all(
    fastqs: List[Path],
    pipeline: Path,
    output: Path,
    threads: int,
    verbose: bool,
    fastp_args: Dict[str, str],
    yes: bool,
) -> None:
    """iterate over and merge all samples

    Args:
        fastqs: List of all fastq files.
        pipeline: Directory for all intermediary files.
        output: Directory for final merged fastq files.
        threads: Number of threads for starcode to use.
        verbose: If true, show subcommand output.
        fastp_args: Extra arguments passed to fastp.
        yes: If true, skip confirmation check.
    """

    for d in [pipeline, output]:
        d.mkdir(exist_ok=True)

    pefastqs = get_pefastqs(fastqs)

    confirm_samples(list(pefastqs), yes)

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

        term.process(status="end")

    term.print("\n[green]FINISHED!")
    sys.exit()
