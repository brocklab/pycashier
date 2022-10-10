from pathlib import Path

from rich.status import Status

from .term import term
from .utils import check_output, extract_csv_column, run_cmd


def cluster(
    sample: str,
    pipeline: Path,
    ratio: int,
    distance: int,
    quality: int,
    threads: int,
    verbose: bool,
    status: Status,
) -> None:
    """cluster the barcodes using starcode

    Args:
        sample: Name of the sample.
        pipeline: Directory for all intermediary files.
        ratio: Clustering ratio for starcode.
        distance: Levenstein distance for starcode.
        quality: PHred quality cutoff for filenames.
        threads: Number of threads for starcode to use.
        verbose: If true, show subcommand output.
        status: Console status to suspend for stderr printing.
    """

    extracted_csv = pipeline / f"{sample}.q{quality}.barcodes.tsv"
    clustered = pipeline / f"{sample}.q{quality}.barcodes.r{ratio}d{distance}.tsv"

    if check_output(
        clustered,
        "clustering barcodes w/ [b]starcode[/]",
    ):

        if not extracted_csv.with_suffix(".c2.tsv").is_file():
            # ? if this file exists this wont be reached and pycashier won't know what the "input_file" is
            # TODO: refactor so input_file isn't unbound
            input_file = extract_csv_column(extracted_csv, 2)

        command = f"starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {clustered}"

        run_cmd(command, sample, clustered, verbose, status)

        input_file.unlink()

        term.process("clustering complete")
