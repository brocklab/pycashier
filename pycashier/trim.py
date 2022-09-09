import shlex
import shutil
import subprocess
import sys

from .term import term
from .utils import fastq_to_csv


def trim(
    sample,
    pipeline,
    fastq,
    quality,
    unqualified_percent,
    fastp_args,
    error,
    threads,
    length,
    distance,
    upstream_adapter,
    downstream_adapter,
    unlinked_adapters,
    skip_trimming,
    verbose,
):

    json_qc = pipeline / "qc" / f"{sample}.json"
    html_qc = pipeline / "qc" / f"{sample}.html"
    input_file = fastq
    filtered_fastq = pipeline / f"{sample}.q{quality}.fastq"
    filtered_barcode_fastq = pipeline / f"{sample}.q{quality}.barcode.fastq"

    if unlinked_adapters:
        adapter_string = f"-g {upstream_adapter} -a {downstream_adapter}"
    else:
        adapter_string = f"-g {upstream_adapter}...{downstream_adapter}"

    (pipeline / "qc").mkdir(exist_ok=True)

    if not filtered_fastq.is_file():

        term.print(f"[green]{sample}[/green]: quality filtering illumina reads")
        command = f"fastp \
            -i {input_file} \
            -o {filtered_fastq} \
            -q {quality} \
            -u {unqualified_percent} \
            -w {threads} \
            -h {html_qc} \
            -j {json_qc} \
            --dont_eval_duplication \
            {fastp_args or ''}"

        args = shlex.split(command)

        p = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        if p.returncode != 0:
            term.print("[yellow]FASTP OUTPUT:")
            term.print(f"[green]{sample}[/green]: fastp failed")
            term.print(p.stdout)
            sys.exit(1)

        elif verbose:
            term.print("[yellow]FASTP OUTPUT:")
            term.print(p.stdout)

    if skip_trimming:
        shutil.copy(filtered_fastq, filtered_barcode_fastq)

    if not filtered_barcode_fastq.is_file():

        term.print(f"[green]{sample}[/green]: extracting barcodes")

        command = f"cutadapt \
            -e {error} \
            -j {threads} \
            --minimum-length={length - distance} \
            --maximum-length={length + distance} \
            --max-n=0 \
            --trimmed-only \
            {adapter_string} \
            -n 2 \
            -o {filtered_barcode_fastq} {filtered_fastq}"

        args = shlex.split(command)

        p = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        if p.returncode != 0 or filtered_barcode_fastq.stat().st_size == 0:
            term.print("[yellow]CUTADAPT OUTPUT:")
            term.print(p.stdout)
            term.print(f"[green]{sample}[/green]: Failed to extract reads for sample")
            term.print("see above for cutadapt output")
            sys.exit()

        elif verbose:
            term.print("[yellow]CUTADAPT OUTPUT:")
            term.print(p.stdout)

        term.print(f"[green]{sample}[/green]: extraction and filtering complete")

    else:
        term.print(f"[green]{sample}[/green]: skipping extraction")

    barcodes_out = pipeline / f"{sample}.q{quality}.barcodes.tsv"

    if not barcodes_out.is_file():
        term.print(f"[green]{sample}[/green]: converting fastq to tsv")
        fastq_to_csv(filtered_barcode_fastq, barcodes_out)
    else:
        term.print(f"[green]{sample}[/green]: skipping fastq to tsv conversion")
