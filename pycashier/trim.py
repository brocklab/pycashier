import shutil
from pathlib import Path
from typing import Dict

from rich.status import Status

from .term import term
from .utils import check_output, fastq_to_tsv, run_cmd


def trim(
    sample: str,
    pipeline: Path,
    fastq: Path,
    quality: int,
    unqualified_percent: float,
    fastp_args: Dict[str, str],
    error: float,
    threads: int,
    length: int,
    distance: int,
    upstream_adapter: str,
    downstream_adapter: str,
    unlinked_adapters: bool,
    skip_trimming: bool,
    verbose: bool,
    status: Status,
) -> None:
    """peform quality filtering and extraction

    Args:
        sample: Name of sample.
        pipeline: Directory for all intermediary files.
        fastq: Path to fastq for sample.
        quality: PHred quality cutoff for filenames.
        unqualified_percent: Percent of bases that may fall below quality cutoff.
        fastp_args: Extra arguments passed to fastp.
        error: Error rate used by cutadapt.
        threads: Number of threads for starcode to use.
        length: Expected lenth of barcode.
        distance: Levenstein distance for starcode.
        upstream_adapter: 5' barcode flanking sequence.
        downstream_adapter: 3' barcode flanking sequence.
        unlinked_adapters: If true use unlinked_adapters with cutadapt.
        skip_trimming: Skip fastp adapter trimming step.
        verbose: If true, show subcommand output.
        status: Rich.console status to suspend for stderr printing.
    """

    json, html = (pipeline / "qc" / f"{sample}.{ext}" for ext in ("json", "html"))
    filtered_fastq, filtered_barcode_fastq = (
        pipeline / f"{sample}.q{quality}.{ext}" for ext in ("fastq", "barcode.fastq")
    )

    adapter_string = (
        f"-g {upstream_adapter} -a {downstream_adapter}"
        if unlinked_adapters
        else f"-g {upstream_adapter}...{downstream_adapter}"
    )

    (pipeline / "qc").mkdir(exist_ok=True)

    if check_output(filtered_fastq, "quality filtering reads w/ [b]fastp[/]"):

        command = (
            "fastp "
            f"-i {fastq} "
            f"-o {filtered_fastq} "
            f"-q {quality} "
            f"-u {unqualified_percent} "
            f"-w {threads} "
            f"-h {html} "
            f"-j {json} "
            "--dont_eval_duplication "
            f"{fastp_args or ''}"
        )

        run_cmd(command, sample, filtered_fastq, verbose, status)

    if skip_trimming:
        shutil.copy(filtered_fastq, filtered_barcode_fastq)

    if check_output(filtered_barcode_fastq, "extracting barcodes w/ [b]cutadapt[/]"):

        command = (
            "cutadapt "
            f"-e {error} "
            f"-j {threads} "
            f"--minimum-length={length - distance} "
            f"--maximum-length={length + distance} "
            f"--max-n=0 "
            f"--trimmed-only "
            f"{adapter_string} "
            "-n 2 "
            f"-o {filtered_barcode_fastq} {filtered_fastq}"
        )

        run_cmd(command, sample, filtered_barcode_fastq, verbose, status)
        term.process("filtering and extraction complete")

    barcodes_out = pipeline / f"{sample}.q{quality}.barcodes.tsv"

    if check_output(barcodes_out, "converting fastq to tsv"):
        fastq_to_tsv(filtered_barcode_fastq, barcodes_out)
