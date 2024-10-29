from __future__ import annotations

from pathlib import Path

import polars as pl
from polars.exceptions import ComputeError, NoDataError

try:
    import pysam
except ImportError:
    pass

from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

from .term import term


# pysam types are finicky
def sam_to_name_labeled_fastq(
    sample: str, sam_file: Path, out_file: Path
) -> bool | None:
    """convert sam file to metadata labeled fastq

    Args:
        sample: Name of sample.
        sam_file: Sam file to convert.
        out_file: Converted fastq file.
        status: Rich.console status to suspend for stderr printing.
    """

    # if the file is a sam file this is the only way I can find in the
    # pysam API to get the total number of reads
    # we really only need this for the progess bar though
    try:
        with pysam.AlignmentFile(  # type: ignore
            str(sam_file.absolute()),
            "r",
            check_sq=False,
            check_header=False,
        ) as sam:
            with term.process("getting sam size"):
                sam_length = sam.count()
    except ValueError:
        term.log.error(f"Couldn't load sam file:{sam_file}. Is it the correct format?")
        return True

    # we don't care about indicies or genomes. since cutadapt will do the heavy lifting here
    with open(out_file, "w") as f_out, pysam.AlignmentFile(
        str(sam_file.absolute()),
        "r",
        check_sq=False,
        check_header=False,  # type: ignore
    ) as sam:
        with term._no_status(), Progress(
            SpinnerColumn("point", style="bright_magenta"),
            *Progress.get_default_columns(),
            "Elapsed:",
            TimeElapsedColumn(),
            transient=True,
            console=term._console,
        ) as progress:
            task = progress.add_task("sam -> fastq", total=sam_length)

            for record in sam.fetch(until_eof=True):
                tagdict = dict(record.tags)  # type: ignore
                cell_barcode = None
                if "CB" in tagdict.keys():
                    cell_barcode = tagdict["CB"].split("-")[0]
                elif "CR" in tagdict.keys():
                    cell_barcode = tagdict["CR"]

                umi = None
                if "UB" in tagdict.keys():
                    umi = tagdict["UB"]
                elif "UR" in tagdict.keys():
                    umi = tagdict["UR"]

                if cell_barcode and umi:
                    qualities = record.query_qualities
                    ascii_qualities = "".join([chr(q + 33) for q in qualities])  # type: ignore

                    f_out.write(f"@{record.query_name}_{umi}_{cell_barcode}\n")
                    f_out.write(f"{record.query_sequence}\n+\n{ascii_qualities}\n")

                progress.advance(task)


def labeled_fastq_to_tsv(in_file: Path, out_file: Path) -> bool | None:
    """convert labeled fastq to tsv

    Args:
        in_file: Fastq to convert to tsv.
        out_file: Converted tsv file.
    Return:
        1 if failure
    """
    try:
        (
            pl.scan_csv(in_file, has_header=False, separator="\t")
            .select(
                pl.all()
                .gather_every(4)
                .str.splitn("_", 3)
                .struct.rename_fields(["info", "umi", "cell"])
                .alias("info"),
                pl.all().gather_every(4, offset=1).alias("barcode"),
            )
            .unnest("info")
            .collect()
            .write_csv(out_file, separator="\t")
        )
    except ComputeError:
        term.log.error(
            f"failed to convert fastq to tsv: {in_file}\n"
            "ensure fastq was not corrupted and contains all reads"
        )
        return True
    except NoDataError:
        term.log.error(
            f"failed to convert fastq to tsv: {in_file}\n"
            "no reads found, check cutadapt output"
        )
        return True
