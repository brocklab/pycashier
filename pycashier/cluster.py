import shlex
import subprocess

from .term import term
from .utils import extract_csv_column


def cluster(sample, pipeline, ratio, distance, quality, threads, verbose):

    extracted_csv = pipeline / f"{sample}.q{quality}.barcodes.tsv"
    output_file = pipeline / f"{sample}.q{quality}.barcodes.r{ratio}d{distance}.tsv"

    if not output_file.is_file():
        if not extracted_csv.with_suffix(".c2.tsv").is_file():
            input_file = extract_csv_column(extracted_csv, 2)

        term.print(f"[green]{sample}[/green]: clustering barcodes")
        command = f"starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {output_file}"

        p = subprocess.run(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        if verbose:
            term.print(
                "[yellow]STARCODE OUTPUT:[/yellow]\n",
                "\n".join(
                    [
                        line
                        for line in p.stdout.splitlines()
                        if not line.startswith("progress")
                    ]
                ),
            )
        input_file.unlink()

        term.print(f"[green]{sample}[/green]: clustering complete")

    else:

        term.print(f"[green]{sample}[/green]: skipping clustering")
