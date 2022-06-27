import multiprocessing
import sys

from rich import box
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from .term import console
from .utils import get_filter_count

SYS_THREADS = multiprocessing.cpu_count()


def make_sample_check_table(
    samples, pipeline, output, quality, ratio, distance, filter, offset, queue_all
):
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
        # filter_expr = f"min{filter['filter_count']}"
        filter_expr = "min(N)"
    else:
        # filter_expr=f"min({filter['filter_percent']}%)"
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

    console.print(
        Panel.fit(
            table,
            title="Queue",
        )
    )

    console.print(
        f"There are {len(samples)-len(processed_samples)} samples to finish processing.\n"
    )

    return processed_samples


def check_in_dir(sample, suffix, directory):
    filepath = f"{sample}{suffix}"
    if directory / filepath in directory.glob(f"*{suffix}"):
        return "[bold green]\u2713"
    else:
        return "[yellow]Queued"


def make_row(sample, pipeline, output, quality, ratio, distance, filter, offset):

    # start the table row
    row = []
    row.append(check_in_dir(sample, f".q{quality}.fastq", pipeline))
    row.append(check_in_dir(sample, f".q{quality}.barcodes.tsv", pipeline))
    row.append(
        check_in_dir(sample, f".q{quality}.barcodes.r{ratio}d{distance}.tsv", pipeline)
    )
    if row[-1] == "[bold green]\u2713":
        if "filter_percent" in filter.keys():
            filter_count = get_filter_count(
                pipeline / f"{sample}.q{quality}.barcodes.r{ratio}d{distance}.tsv",
                filter["filter_percent"],
            )
        else:
            filter_count = filter["filter_count"]
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
    fastqs,
    pipeline,
    output,
    quality,
    ratio,
    distance,
    filter,
    offset,
):
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

    if len(processed_samples) != len(samples) and not Confirm.ask(
        "Continue with these samples?"
    ):
        sys.exit()

    return [f for sample, f in samples.items() if sample in processed_samples]


def print_params(ctx):
    params = ctx.params
    params.pop("save_config")
    params = {k: v for k, v in params.items() if v is not None}

    grid = Table.grid(expand=True)
    grid.add_column(justify="right", style="bold cyan")
    grid.add_column(justify="center")
    grid.add_column(style="yellow")

    for key, value in params.items():
        grid.add_row(key, ": ", str(value))

    console.print(
        Panel.fit(grid, title=f"{ctx.info_name.capitalize()} Parameters", padding=1)
    )
    if not ctx.info_name == "combine":
        if params["threads"] == 1 and params["threads"] <= SYS_THREADS / 4:
            console.print(
                f"[dim]Using {params['threads']} of {SYS_THREADS} available threads.\n"
                "[i]HINT[/]: use `--threads` to increase"
            )
