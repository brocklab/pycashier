from pathlib import Path
from typing import Mapping, Union

from .term import term
from .utils import get_filter_count


def filter_by_percent(
    file_in: Path, filter_percent: float, length: int, offset: int, outdir: Path
) -> None:
    """filter clusted barcodes with nominal abundance cutoff

    Args:
        file_in: Path to clustered barcode counts.
        filter_percent: Minimum percent of total cutoff.
        length: Expected lenth of barcode.
        offset: Acceptable insertion or deletion from expected length in final sequences.
        output: Directory for final tsv files.
    """

    # TODO: docstring

    filter_by_count(
        file_in, get_filter_count(file_in, filter_percent), length, offset, outdir
    )


def filter_by_count(
    file_in: Path, filter_count: int, length: int, offset: int, output: Path
) -> None:
    """filter clusted barcodes with nominal abundance cutoff

    Args:
        file_in: Path to clustered barcode counts.
        filter_count: Minimum count cutoff.
        length: Expected lenth of barcode.
        offset: Acceptable insertion or deletion from expected length in final sequences.
        output: Directory for final tsv files.
    """

    final = output / f"{file_in.stem}.min{filter_count}_off{offset}{file_in.suffix}"

    with open(file_in, "r") as csv_in, open(final, "w") as csv_out:
        for line in csv_in:
            linesplit = line.split("\t")
            if (
                int(linesplit[1]) >= filter_count
                and abs(len(linesplit[0]) - length) <= offset
            ):
                csv_out.write(f"{linesplit[0]}\t{linesplit[1]}")

    if final.stat().st_size == 0:
        term.print(
            "[yellow]WARNING[/]: no barcodes passed final length and abundance filters"
        )


def read_filter(
    sample: str,
    pipeline: Path,
    output: Path,
    length: int,
    offset: int,
    filter: Mapping[str, Union[int, float]],
    quality: int,
    ratio: int,
    distance: int,
) -> None:
    """filter clusted barcodes with final abundance cutoff

    Args:
        sample: Name of the sample.
        pipeline: Directory for all intermediary files.
        output: Directory for final tsv files.
        length: Expected lenth of barcode.
        offset: Acceptable insertion or deletion from expected length in final sequences.
        filter: Dictionary defining how to filter final clustered barcodes.
        quality: PHred quality cutoff for filenames.
        ratio: Clustering ratio for starcode.
        distance: Levenstein distance for starcode.
    """

    file_in = pipeline / f"{sample}.q{quality}.barcodes.r{ratio}d{distance}.tsv"

    if "filter_count" in filter.keys():
        term.process(
            f"post-clustering filtering w/ [b]{filter['filter_count']}[/] read cutoff"
        )

        filter_by_count(file_in, int(filter["filter_count"]), length, offset, output)

    else:
        term.process(
            f"post-clustering filtering w/ [b]{filter['filter_percent']}[/] % cutoff"
        )

        filter_by_percent(file_in, filter["filter_percent"], length, offset, output)
