import shlex
import subprocess
from pathlib import Path

from .console import console
from .utils import extract_csv_column


def cluster(sample, ratio, distance, quality, threads, **kwargs):
    pipeline = Path(kwargs["pipelinedir"])

    extracted_csv = pipeline / f"{sample}.barcodes.q{quality}.tsv"

    if not extracted_csv.with_suffix(".c2.tsv").is_file():
        input_file = extract_csv_column(extracted_csv, 2)

    output_file = pipeline / f"{sample}.barcodes.q{quality}.r{ratio}d{distance}.tsv"

    if not output_file.is_file():
        console.log(f"[green]{sample}[/green]: clustering barcodes")
        command = f"starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {output_file}"

        args = shlex.split(command)

        p = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        if kwargs["verbose"]:
            console.print("[yellow]STARCODE OUTPUT:")
            console.print(
                "\n".join(
                    [
                        line
                        for line in p.stdout.splitlines()
                        if not line.startswith("progress")
                    ]
                )
            )

        console.log(f"[green]{sample}[/green]: clustering complete")

    else:
        console.log(f"[green]{sample}[/green]: skipping clustering")
