from __future__ import annotations

from pathlib import Path

import polars as pl

from .options import PycashierOpts
from .term import term
from .utils import get_filter_count


def filter_by_percent(
    file_in: Path, filter_percent: float, length: int, offset: int, outdir: Path
) -> bool | None:
    """filter clustered barcodes with nominal abundance cutoff

    Args:
        file_in: Path to clustered barcode counts.
        filter_percent: Minimum percent of total cutoff.
        length: Expected lenth of barcode.
        offset: Acceptable insertion or deletion from length in final sequences.
        output: Directory for final tsv files.
    """

    return filter_by_count(
        file_in, get_filter_count(file_in, filter_percent), length, offset, outdir
    )


def filter_by_count(
    file_in: Path, filter_count: int, length: int, offset: int, output: Path
) -> bool | None:
    """filter clusted barcodes with nominal abundance cutoff

    Args:
        file_in: Path to clustered barcode counts.
        filter_count: Minimum count cutoff.
        length: Expected lenth of barcode.
        offset: Acceptable insertion or deletion from length in final sequences.
        output: Directory for final tsv files.
    """

    final = output / f"{file_in.stem}.min{filter_count}_off{offset}{file_in.suffix}"

    # TODO: TRY/EXCEPT
    df = (
        pl.scan_csv(
            file_in, separator="\t", has_header=False, new_columns=["barcode", "count"]
        )
        .filter(
            (pl.col("count") > filter_count)
            & (
                (pl.col("barcode").str.len_chars().cast(pl.Int64) - length).abs()
                <= offset
            )
        )
        .collect()
    )

    df.write_csv(final, separator="\t")
    if df.height == 0:
        term.log.warning("no barcodes passed final length and abundance filters")
        return True


def read_filter(
    clustered_counts: Path,
    opts: PycashierOpts,
) -> bool | None:
    """filter clusted barcodes with final abundance cutoff

    Args:
        sample: Name of the sample.
        opts: pycashier options
    """

    if opts.filter_count is not None:
        term.log.debug(
            f"post-clustering filtering with [b]{opts.filter_count}[/] read cutoff"
        )
        return filter_by_count(
            clustered_counts,
            int(opts.filter_count),
            opts.length,
            opts.offset,
            opts.output,
        )

    else:
        term.log.debug(
            f"post-clustering filtering with [b]{opts.filter_percent}[/] % cutoff"
        )

        return filter_by_percent(
            clustered_counts,
            opts.filter_percent,
            opts.length,
            opts.offset,
            opts.output,
        )
