from pathlib import Path
from typing import Dict, Tuple

import polars as pl

from .options import PycashierOpts
from .term import term


def gen_queries(sample: str, file: Path) -> pl.LazyFrame:
    return pl.scan_csv(file, separator="\t").with_columns(
        sample=pl.lit(sample),
        percent=(pl.col("count") / pl.col("count").sum() * 100).round(5),
    )


def parse_column_not_found_error(message: str) -> Tuple[str, str]:
    contents = message.splitlines()
    file = contents[4].split()[2]
    return contents[0], file


def receipt(files: Dict[str, Path], opts: PycashierOpts) -> None:
    term.log.info(f"Combining output files for {len(files)} samples.")
    term.log.debug("samples: " + ", ".join(files))

    lzdf = pl.concat(gen_queries(sample, file) for sample, file in files.items())
    if not opts.no_overlap:
        lzdf = lzdf.join(
            lzdf.group_by(pl.col("barcode"))
            .agg(
                pl.col("sample").alias("samples").sort(),
                pl.col("sample").len().alias("n_samples"),
            )
            .with_columns(pl.col("samples").list.join(";")),
            on=pl.col("barcode"),
        ).sort("sample", "count", "barcode", descending=True)
    try:
        lzdf.collect().write_csv(opts.output, separator="\t")
    except pl.ColumnNotFoundError as e:
        col, file = parse_column_not_found_error(e.args[0])
        term.log.error(f"missing column [b red]{col}[/] in [b]{file}[/]")
        term.log.error(f"check files in input directory: [b]{opts.input_}[/]")
        term.quit()
    except pl.ComputeError:
        term.log.error("unexpected error processing inputs")
        term.log.error(
            f"ensure [b]{opts.input_}[/] contains [b]pycashier extract[/] outputs"
        )
        term.quit()
