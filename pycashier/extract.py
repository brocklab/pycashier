import shlex
import subprocess
import sys
from pathlib import Path

from .console import console
from .utils import fastq_to_csv


def extract(
    sample,
    fastq,
    error_rate,
    threads,
    barcode_length,
    min_barcode_length,
    upstream_adapter,
    downstream_adapter,
    unlinked_adapters,
    quality,
    **kwargs,
):

    pipeline = Path(kwargs["pipelinedir"])
    json_qc = pipeline / "qc" / f"{sample}.json"
    html_qc = pipeline / "qc" / f"{sample}.html"
    # barcode_fastq = pipeline / f"{sample}.barcode.fastq"
    input_file = fastq
    # filtered_barcode_fastq = pipeline / f"{sample}.barcode.q{quality}.fastq"
    filtered_fastq = pipeline / f"{sample}.q{quality}.fastq"
    filtered_barcode_fastq = pipeline / f"{sample}.q{quality}.barcode.fastq"

    if unlinked_adapters:
        adapter_string = f"-g {upstream_adapter} -a {downstream_adapter}"
    else:
        adapter_string = f"-g {upstream_adapter}...{downstream_adapter}"

    (pipeline / "qc").mkdir(exist_ok=True)

    if not filtered_barcode_fastq.is_file():

        console.log(f"[green]{sample}[/green]: extracting and filtering barcodes")

        command = f"fastp \
            -i {input_file} \
            -o {filtered_fastq} \
            -q {quality} \
            -u 80 \
            -w {threads} \
            -h {html_qc} \
            -j {json_qc} \
            --dont_eval_duplication"

        args = shlex.split(command)

        p = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        if p.returncode != 0:
            console.print("[yellow]FASTP OUTPUT:")
            console.print(f"[green]{sample}[/green]: fastp failed")
            console.print(p.stdout)
            sys.exit(1)

        elif kwargs["verbose"]:
            console.print("[yellow]FASTP OUTPUT:")
            console.print(p.stdout)

        command = f"cutadapt \
            -e {error_rate} \
            -j {threads} \
            --minimum-length={min_barcode_length} \
            --maximum-length={barcode_length} \
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

        if filtered_barcode_fastq.stat().st_size == 0:
            console.print("[yellow]CUTADAPT OUTPUT:")
            console.print(p.stdout)
            console.print(
                f"[green]{sample}[/green]: Failed to extract reads for sample"
            )
            console.print("see above for cutadapt output")
            sys.exit()

        elif kwargs["verbose"]:
            console.print("[yellow]CUTADAPT OUTPUT:")
            console.print(p.stdout)

        # barcode_fastq.unlink()

        console.log(f"[green]{sample}[/green]: extraction and filtering complete")

    else:
        console.log(f"[green]{sample}[/green]: skipping extraction")

    barcodes_out = pipeline / f"{sample}.barcodes.q{quality}.tsv"

    if not barcodes_out.is_file():
        console.log(f"[green]{sample}[/green]: converting fastq to tsv")
        fastq_to_csv(filtered_barcode_fastq, barcodes_out)
    else:
        console.log(f"[green]{sample}[/green]: skipping fastq to tsv conversion")
