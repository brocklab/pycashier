from __future__ import annotations

import multiprocessing
from typing import Dict, List

import click
from click.core import ParameterSource
from rich import box
from rich.table import Table
from rich.tree import Tree

from .options import PycashierOpts
from .sample import ExtractSample, MergeSample, Sample, ScrnaSample
from .term import term

SYS_THREADS = multiprocessing.cpu_count()


def show_sample_queue(
    samples: List[ExtractSample],
    completed_samples: List[ExtractSample],
    queue_all: bool,
    opts: PycashierOpts,
) -> None:
    """print formatted table for sample queue

    Args:
        queue_all: If true, skip output check and queue all samples.
        opts
    """

    table = Table(box=box.SIMPLE, header_style="bold cyan", collapse_padding=True)
    table.add_column(
        "sample",
        justify="center",
        style="green",
        no_wrap=True,
    )
    table.add_column(f"q{opts.quality}", justify="center")
    table.add_column("barcodes", justify="center")
    table.add_column(
        f"r{opts.ratio}d{opts.distance}",
        justify="center",
    )

    filter_expr = ("min(%)") if opts.filter_percent else "min(N)"
    table.add_column(f"{filter_expr}_off{opts.offset}", justify="center")

    if queue_all:
        for sample in samples:
            table.add_row(*([f"[bold yellow]{sample.name}"] + ["[yellow]Queued"] * 4))
    else:
        for sample in samples:
            color = "green" if sample.completed else "yellow"
            row = [f"[bold {color}]{sample.name}"] + [
                "[bold green]\u2713" if v else "[yellow]Queued"
                for v in sample.files_exist.values()
            ]
            table.add_row(*row)

    term.print(
        table,
        f"There are [bold cyan]{len(samples)-len(completed_samples)}[/] samples to finish processing.\n",
    )


def confirm_extract_samples(samples: List[ExtractSample], opts: PycashierOpts) -> None:
    queue_all = not opts.pipeline.is_dir()
    completed_samples = [sample for sample in samples if sample.completed]
    show_sample_queue(
        samples=samples,
        completed_samples=completed_samples,
        queue_all=queue_all,
        opts=opts,
    )

    if not opts.yes and (
        len(completed_samples) != len(samples)
        and not term.confirm("Continue with these samples?")
    ):
        term.quit(0)


def fmt_sample_list(samples: set[Sample]) -> str:
    return ", ".join(sorted((sample.name for sample in samples)))


def confirm_samples(
    samples: List[MergeSample] | List[ScrnaSample], opts: PycashierOpts
) -> None:
    completed = set(filter(lambda sample: sample.completed, samples))
    incomplete = set(samples) - completed

    term.print()
    if completed:
        term.print(f"[hl]Processed[/]: {fmt_sample_list(completed)}")
    if incomplete:
        term.print(f"[hl]To be processed[/]: {fmt_sample_list(incomplete)}")
    if not opts.yes and incomplete and not term.confirm("Continue with these samples?"):
        term.quit(0)


def print_params(ctx: click.Context) -> None:
    """show all parameters prior to run"""

    params = ctx.params
    verbose = params.pop("verbose")
    params.pop("save_config", None)
    params.pop("yes", None)
    params = {
        (k if k != "input_" else "input"): v for k, v in params.items() if v is not None
    }

    term.log.info("[bold]parameters")

    param_maps: Dict[str, Dict] = {"cli": {}, "config": {}, "default": {}}
    for k, v in params.items():
        source = ctx.get_parameter_source(k)
        if source == ParameterSource.DEFAULT:
            param_maps["default"][k] = v
        elif source == ParameterSource.DEFAULT_MAP:
            param_maps["config"][k] = v
        # elif source == ParameterSource.COMMANDLINE
        # params[input] is None and we don't use other ParameterSource's
        else:
            param_maps["cli"][k] = v

    for header, param_map in param_maps.items():
        if len(param_map) == 0:
            continue
        tree = Tree(f"[italic]{header}", style="bold")
        for k, v in param_map.items():
            if k == "samples":
                sample_tree = tree.add(f"[bold][cyan]{k.replace('_',' ')}[/cyan]:")
                for sample in v.split(","):
                    sample_tree.add(f"[yellow]{sample}[/yellow]")
            else:
                tree.add(
                    f"[bold][cyan]{k.replace('_', ' ')}[/cyan]: [yellow]{v}[/yellow]"
                )
        with term._console.capture() as capture:
            term.print(tree)

        if header == "default" and not verbose:
            term.log.debug(capture.get())
        else:
            term.log.info(capture.get())

    if not verbose:
        term.print("[dim]use -v/--verbose to see all parameters")

    if not ctx.info_name == "receipt":
        if params["threads"] == 1 and params["threads"] <= SYS_THREADS / 4:
            term.print(
                f"[dim]Only using {params['threads']} of {SYS_THREADS} available threads..."
            )
