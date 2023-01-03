import multiprocessing
import sys
from pathlib import Path
from typing import List, Mapping, Union

import click
from rich import box
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from .term import term
from .utils import get_filter_count

SYS_THREADS = multiprocessing.cpu_count()


def make_sample_check_table(
    samples: List[str],
    pipeline: Path,
    output: Path,
    quality: int,
    ratio: int,
    distance: int,
    filter: Mapping[str, Union[int, float]],
    offset: int,
    queue_all: bool,
) -> List[str]:
    """print formatted table for sample queue

    Args:
        samples: Names of the samples.
        pipeline: Directory for all intermediary files.
        output: Directory for final tsv files.
        quality: PHred quality cutoff for filenames.
        ratio: Clustering ratio for starcode.
        distance: Levenstein distance for starcode.
        filter: Dictionary defining how to filter final clustered barcodes.
        offset: Acceptable insertion or deletion from expected length in final sequences.
        queue_all: If true, skip output check and queue all samples.
    """

    processed_samples = []
    table = Table(box=box.SIMPLE, header_style="bold cyan", collapse_padding=True)
    table.add_column(
        "sample",
        justify="center",
        style="green",
        no_wrap=True,
    )
    table.add_column(f"q{quality}", justify="center")
    table.add_column("barcodes", justify="center")
    table.add_column(
        f"r{ratio}d{distance}",
        justify="center",
    )
    if "filter_count" in filter.keys():
        filter_expr = "min(N)"
    else:
        filter_expr = "min(%)"
    table.add_column(f"{filter_expr}_off{offset}", justify="center")

    for sample in samples:
        if not queue_all:
            row = make_row(
                sample, pipeline, output, quality, ratio, distance, filter, offset
            )
            if "[bold green]" in row[0]:
                processed_samples.append(sample)
        else:
            row = [f"[bold yellow]{sample}"] + ["[yellow]Queued"] * 4

        table.add_row(*row)

    term.print(
        Panel.fit(table, title=term.style_title("Queue"), border_style="border"),
        f"\nThere are {len(samples)-len(processed_samples)} samples to finish processing.\n",
    )

    # TODO: seperate table generation from sample checks.
    return processed_samples


def check_in_dir(sample: str, suffix: str, directory: Path) -> str:
    """check the directory for expected file

    Args:
        sample: Name of sample.
        suffix: File name contents following sample.
        directory: Place to look for file.
    Returns:
        Green check if true. Yellow 'Queued' if false.
    """
    filepath = f"{sample}{suffix}"
    if directory / filepath in directory.glob(f"*{suffix}"):
        return "[bold green]\u2713"
    else:
        return "[yellow]Queued"


def make_row(
    sample: str,
    pipeline: Path,
    output: Path,
    quality: int,
    ratio: int,
    distance: int,
    filter: Mapping[str, Union[int, float]],
    offset: int,
) -> List[str]:
    """generate row for sample queue

    Args:
        sample: Name of the sample.
        pipeline: Directory for all intermediary files.
        output: Directory for final tsv files.
        quality: PHred quality cutoff for filenames.
        ratio: Clustering ratio for starcode.
        distance: Levenstein distance for starcode.
        filter: Dictionary defining how to filter final clustered barcodes.
        offset: Acceptable insertion or deletion from expected length in final sequences.
    Returns:
        List of fastq files for samples not finished processing.
    """

    # start the table row
    row = []
    row.append(check_in_dir(sample, f".q{quality}.fastq", pipeline))
    row.append(check_in_dir(sample, f".q{quality}.barcodes.tsv", pipeline))
    row.append(
        check_in_dir(sample, f".q{quality}.barcodes.r{ratio}d{distance}.tsv", pipeline)
    )
    if row[-1] == "[bold green]\u2713":
        if "filter_percent" in filter:
            filter_count = get_filter_count(
                pipeline / f"{sample}.q{quality}.barcodes.r{ratio}d{distance}.tsv",
                float(filter["filter_percent"]),
            )
        else:
            filter_count = int(filter["filter_count"])
        row.append(
            check_in_dir(
                sample,
                f".q{quality}.barcodes.r{ratio}d{distance}.min{filter_count}_off{offset}.tsv",
                output,
            )
        )

    if set(row[1:]) == {"[bold green]\u2713"}:
        row = [f"[bold green]{sample}"] + row
    else:
        row.extend(["[yellow]Queued"] * (4 - len(row)))
        row = [f"[bold yellow]{sample}"] + row

    return row


def sample_check(
    fastqs: List[Path],
    pipeline: Path,
    output: Path,
    quality: int,
    ratio: int,
    distance: int,
    filter: Mapping[str, Union[int, float]],
    offset: int,
    yes: bool,
) -> List[Path]:
    """check for existence of file outputs for a set of samples

    Args:
        fastqs: List of fastq files.
        pipeline: Directory for all intermediary files.
        output: Directory for final tsv files.
        quality: PHred quality cutoff for filenames.
        ratio: Clustering ratio for starcode.
        distance: Levenstein distance for starcode.
        filter: Dictionary defining how to filter final clustered barcodes.
        offset: Acceptable insertion or deletion from expected length in final sequences.
        yes: If true, skip confirmation check.
    Returns:
        List of fastq files for samples not finished processing.
    """

    samples = {f.name.split(".")[0]: f for f in fastqs}
    queue_all = not pipeline.is_dir()
    processed_samples = make_sample_check_table(
        sorted(samples.keys()),
        pipeline,
        output,
        quality,
        ratio,
        distance,
        filter,
        offset,
        queue_all,
    )

    if not yes and (
        len(processed_samples) != len(samples)
        and not term.confirm("Continue with these samples?")
    ):
        sys.exit()
    if not yes and len(processed_samples) != len(samples):
        term.print()

    return [f for sample, f in samples.items() if sample in processed_samples]


def print_params(ctx: click.Context) -> None:
    """show all parameters prior to run"""

    params = ctx.params
    params.pop("save_config")
    params = {k: v for k, v in params.items() if v is not None}

    # TODO: until a refactor of params/config we'll just hard code a new dictionary
    # we want input to still be at the top of the list of parameters...
    # we could instead hard code a priority list of the parameters then insertion order is irrelevant
    params = {(k if k != "input_" else "input"): v for k, v in params.items()}

    grid = Table.grid(expand=True)
    grid.add_column(justify="right", style="bold cyan")
    grid.add_column(justify="center")
    grid.add_column(style="yellow")

    for key, value in params.items():
        grid.add_row(key, ": ", str(value))

    group: Union[Group, Table] = (
        Group(grid, Align(f"[dim]including {ctx.obj['configfile']}", align="center"))
        if "config-loaded" in ctx.obj
        else grid
    )

    term.print(
        Panel.fit(
            group,
            title=term.style_title(f"{ctx.info_name.capitalize()} Parameters"),  # type: ignore
            border_style="border",
        )
    )

    # if "config_file" in ctx.obj:
    #     grid.add_row("loaded config", ": ", str(ctx.obj["config_file"]))

    if not ctx.info_name == "combine":
        if params["threads"] == 1 and params["threads"] <= SYS_THREADS / 4:
            term.print(
                f"[dim]Only using {params['threads']} of {SYS_THREADS} available threads..."
            )
