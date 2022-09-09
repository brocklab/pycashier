import shlex
import subprocess
import sys

from .term import term
from .utils import exit_status, extract_csv_column


def cluster(sample, pipeline, ratio, distance, quality, threads, verbose, status):

    extracted_csv = pipeline / f"{sample}.q{quality}.barcodes.tsv"
    output_file = pipeline / f"{sample}.q{quality}.barcodes.r{ratio}d{distance}.tsv"

    if not output_file.is_file():
        if not extracted_csv.with_suffix(".c2.tsv").is_file():
            # ? if this file exists this wont be reached and pycashier won't know what the "input_file" is
            input_file = extract_csv_column(extracted_csv, 2)

        term.print(f"[green]{sample}[/green]: clustering barcodes")
        command = f"starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {output_file}"

        p = subprocess.run(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        if verbose or exit_status(p, output_file):
            term.subcommand(
                sample,
                "starcode",
                command,
                # TODO: is stderr causing this?
                "\n".join(
                    [
                        line
                        for line in p.stdout.splitlines()
                        if not line.startswith("progress")
                    ]
                ),
            )

        if exit_status(p, output_file):
            status.stop()
            term.print(
                f"[StarcodeError]: starcode failed to cluster sample: [green]{sample}[/green]\n"
                "see above for output",
                err=True,
            )
            sys.exit(1)

        input_file.unlink()

        term.print(f"[green]{sample}[/green]: clustering complete")

    else:

        term.print(f"[green]{sample}[/green]: skipping clustering")
