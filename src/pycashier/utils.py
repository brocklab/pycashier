from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Dict, List

import click
import polars as pl
from polars.exceptions import NoDataError

from .term import term


def filter_input_by_sample(
    candidate_files: List[Path], samples: List[str]
) -> List[Path]:
    """filter candidate fastqs based on user provided samples
    Args:
        candidate_fastqs: all fastq files found in input direcotry
        samples: user provided list of samples
    Returns:
        returns list of accepted fastqs
    """

    found, files, ignored = [], [], []
    for f in candidate_files:
        name, *_ = f.name.split(".")
        if name in samples:
            found.append(name)
            files.append(f)
        else:
            ignored.append(name)

    not_found = set(samples).difference(found)
    if not_found:
        term.print(f"[InputError]: Unknown sample(s) -> {not_found}", err=True)
        term.quit()

    if ignored:
        term.print(f"[dim]ignoring {len(set(ignored))} samples")

    return files


def fastq_to_tsv(in_file: Path, out_file: Path) -> bool | None:
    """convert fastq file to tsv

    Args:
        in_file: Fastq file to convert.
        out_file: TSV file to write to.
    """

    try:
        pl.scan_csv(in_file, has_header=False, separator="\t").select(
            pl.all().gather_every(4).alias("info"),
            pl.all().gather_every(4, offset=1).alias("barcode"),
        ).collect().write_csv(out_file, separator="\t")
    except pl.ComputeError:
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


def extract_csv_column(csv_file: Path, out_file: Path) -> None:
    """get column from csv file

    Args:
        csv_file: File to extract column from.
        out_file: File to write column to.
    """
    pl.scan_csv(csv_file, separator="\t").select(pl.col("barcode")).collect().write_csv(
        out_file, separator="\t", include_header=False
    )


def get_filter_count(file_in: Path, filter_percent: float, quit: bool = False) -> int:
    """calculate filter cutoff

    Args:
        file_in: Clustered lineage counts to filter.
        filter_percent: Percent cutoff of total reads count.
        quit: exit if failure to get filter cutoff
    Returns:
        Minimum nominal cutoff value.
    """
    try:
        sum = (
            pl.scan_csv(
                file_in,
                separator="\t",
                has_header=False,
                new_columns=("barcode", "count"),
            )
            .select(pl.col("count").sum())
            .collect(streaming=True)
            .item()
        )
    except NoDataError:
        term.log.error(
            f"Failed to determine filter cutoff for empty file {file_in}.\n"
            " Please remove it and try again."
        )
        term.quit()
    return int(
        round(
            sum * filter_percent / 100,
            0,
        )
    )


def validate_filter_args(ctx: click.Context) -> Dict[str, float]:
    """validate filter argument from config and CLI

    Args:
        ctx: Click context.
    Returns:
        Dictionary defining the filter type and value.
    """
    if ctx.params["filter_count"] or ctx.params["filter_count"] == 0:
        if ctx.get_parameter_source("filter_percent").value == 3:  # type: ignore
            ctx.params["filter_percent"] = None
            del ctx.params["filter_percent"]
            return {"filter_count": ctx.params["filter_count"]}
        else:
            raise click.BadParameter(
                "`--filter-count` and `--filter-percent` are mutually exclusive"
            )
    else:
        del ctx.params["filter_count"]
        return {"filter_percent": ctx.params["filter_percent"]}


def exit_status(p: subprocess.CompletedProcess, file: Path) -> bool:
    """check command exit status and file size

    Args:
        p: Completed subprocess
        file: File to check for nonzero size.
    Returns:
        True for success, False otherwise.
    """
    return True if p.returncode != 0 or file.stat().st_size == 0 else False


def run_cmd(
    command: str,
    sample: str,
    output: Path,
    verbose: bool,
) -> bool | None:
    """run a subcommand

    Args:
        command: Subcommand to be run in subprocess.
        sample: Name of sample.
        output: file of immediate output.
        verbose: If true, print subcommand output.
    Returns:
        exit code
    """
    cmd_name = command.split()[0]
    p = subprocess.run(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    # remove 'progress: ##%' output from starcode
    stdout = (
        p.stdout
        if not cmd_name == "starcode"
        else "\n".join(
            [line for line in p.stdout.splitlines() if not line.startswith("progress")]
        )
    )

    term.log.debug("subcommand:\n  [b]" + command)
    term.log.debug(
        "subcommand output:\n"
        + "\n".join(("[b]| [/]" + line for line in stdout.splitlines()))
    )
    if exit_status(p, output):
        term.print(
            f"[{cmd_name.capitalize()}Error]: Subprocess for sample failed: [green]{sample}[/green]",
            err=True,
        )
        return True


def check_output(file: Path, message: str) -> bool:
    """check for output file and print message

    Args:
        file: Resulting file of step.
        message: Text to display related to step.
    Returns:
        True for success, False otherwise.
    """
    exists = file.is_file()

    if not exists:
        term.log.debug("missing output file: " + file.name)
        term.log.debug(message)
    else:
        term.log.debug("found output file: " + file.name)
    return exists
