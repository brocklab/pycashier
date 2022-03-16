import sys
from pathlib import Path

import rich_click as click
from rich import box
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from ruamel.yaml import YAML

from ._checks import pre_run_check
from .console import console
from .extract import extract_all
from .merge import merge_all
from .read_filter import get_filter_count
from .single_cell import single_cell
from .utils import combine_outs, get_fastqs

yaml = YAML()

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.MAX_WIDTH = 100

PROG_NAME = "pycashier"
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


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
            border_style=click.rich_click.STYLE_COMMANDS_PANEL_BORDER,
            title="Queue",
            title_align=click.rich_click.ALIGN_COMMANDS_PANEL,
            width=click.rich_click.MAX_WIDTH,
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
        Panel.fit(
            grid,
            border_style=click.rich_click.STYLE_OPTIONS_PANEL_BORDER,
            title=f"{ctx.info_name.capitalize()} Parameters",
            title_align=click.rich_click.ALIGN_OPTIONS_PANEL,
            width=click.rich_click.MAX_WIDTH,
        )
    )


def save_params(ctx):
    params = ctx.params
    save_type = params.pop("save_config")
    try:
        config_file = Path(ctx.obj["config_file"])
    except TypeError:
        raise click.BadParameter("use `--save-config` with a specified `--config-file`")

    if config_file.is_file():
        console.print(f"Updating current config file at [b cyan]{config_file}")
        with config_file.open("r") as f:
            config = yaml.load(f)
    else:
        console.print(f"Staring a config file at [b cyan]{config_file}")
        config = {}

    if save_type == "explicit":
        params = {
            k: v for k, v in params.items() if ctx.get_parameter_source(k).value != 3
        }

    # sanitize the path's for writing to yaml
    for k in ["input", "pipeline", "output"]:
        if k in params.keys():
            params[k] = str(params[k])

    config[ctx.info_name] = params

    with config_file.open("wb") as f:
        yaml.dump(config, f)

    console.print("Exiting...")
    ctx.exit()


def load_params(ctx, param, filename):
    if not filename or ctx.resilient_parsing:
        return

    ctx.default_map = {}
    if Path(filename).is_file():
        with Path(filename).open("r") as f:
            params = yaml.load(f)
        if params:
            ctx.default_map = params.get(ctx.info_name, {})
    else:
        console.print("No config file found. ignoring..")

    ctx.obj = {"config_file": filename}


def init_check(ctx, param, check):
    if not check:
        pre_run_check()


def validate_filter_args(ctx):
    if ctx.params["filter_count"] or ctx.params["filter_count"] == 0:
        if ctx.get_parameter_source("filter_percent").value == 3:
            ctx.params["filter_percent"] = None
            return {"filter_count": ctx.params["filter_count"]}
        else:
            raise click.BadParameter(
                "`--filter-count` and `--filter-percent` are mutually exclusive"
            )
    else:
        return {"filter_percent": ctx.params["filter_percent"]}


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


# Click option definitions
##########################


_output_options = [
    click.option(
        "-o",
        "--output",
        help="output directory",
        default="./outs",
        show_default=True,
        type=click.Path(file_okay=False, path_type=Path),
    ),
    click.option(
        "-p",
        "--pipeline",
        help="pipeline directory",
        default="./pipeline",
        show_default=True,
        type=click.Path(file_okay=False, path_type=Path),
    ),
]

_general_options = [
    click.option(
        "-v", "--verbose", help="print the output of underlying software", is_flag=True
    ),
    click.option(
        "-t",
        "--threads",
        help="number of cpu cores to use",
        default=1,
        show_default=True,
    ),
    click.option(
        "-c",
        "--config",
        type=click.Path(dir_okay=False),
        callback=load_params,
        is_eager=True,
        expose_value=False,
        help="read parameter values from config file",
        show_default=True,
    ),
    click.option(
        "--save-config",
        help="save current params to file specified by `--config`",
        type=click.Choice(["explicit", "full"], case_sensitive=False),
    ),
    click.option(
        "--skip-init-check",
        help="skip runtime dependency check",
        is_flag=True,
        hidden=True,
        expose_value=False,
        callback=init_check,
    ),
]

_trim_options = [
    click.option(
        "-e",
        "--error",
        help="error tolerance supplied to cutadapt",
        default=0.1,
        show_default=True,
    ),
    click.option(
        "-l",
        "--length",
        help="target length of extracted barcode",
        default=20,
        show_default=True,
    ),
    click.option(
        "-ua",
        "--upstream-adapter",
        help="5' sequence flanking barcode",
        default="ATCTTGTGGAAAGGACGAAACACCG",
    ),
    click.option(
        "-da",
        "--downstream-adapter",
        help="3' sequence flanking barcode",
        default="GTTTTAGAGCTAGAAATAGCAAGTT",
    ),
    click.option(
        "--unlinked-adapters", help="run cutadapt using unlinked adapters", is_flag=True
    ),
    click.option(
        "--skip-trimming",
        help="skip cutadapt trimming entirely and use reads as-is",
        is_flag=True,
    ),
]

_quality_options = [
    click.option(
        "-q",
        "--quality",
        help="minimum PHRED quality for filtering reads",
        default=30,
        show_default=True,
    ),
    click.option(
        "-up",
        "--unqualified-percent",
        help="minimum percent of bases which can be below quality threshold",
        default=20,
        show_default=True,
    ),
    click.option(
        "-fa",
        "--fastp-args",
        help="additional arguments provided as a string passed verbatim to fastp",
        type=str,
    ),
]

_cluster_options = [
    click.option(
        "-r",
        "--ratio",
        help="ratio to use for message passing clustering",
        default=3,
        show_default=True,
    ),
    click.option(
        "-d",
        "--distance",
        help="levenshtein distance for clustering",
        default=1,
        show_default=True,
        type=click.IntRange(1, 8),
    ),
]

_filter_options = [
    click.option(
        "-fc",
        "--filter-count",
        help="minium nominal number of reads",
        type=int,
    ),
    click.option(
        "-fp",
        "--filter-percent",
        help="minimum percentage of total reads",
        default=0.005,
        show_default=True,
    ),
    click.option(
        "--offset",
        help="length offset from target barcode length post-clustering",
        default=1,
        show_default=True,
    ),
]
##########################


# Rich Click Option groups
##########################


_general_options_group = {
    "name": "General Options",
    "options": [
        "--help",
        "--verbose",
        "--threads",
        "--config",
        "--save-config",
    ],
}
_trim_options_group = {
    "name": "Trim (Cutadapt) Options",
    "options": [
        "--error",
        "--length",
        "--upstream-adapter",
        "--downstream-adapter",
        "--unlinked-adapters",
        "--skip-trimming",
    ],
}

_input_output_options_group = {
    "name": "Input/Output Options",
    "options": ["--input", "--output", "--pipeline"],
}

click.rich_click.OPTION_GROUPS = {
    "pycashier extract": [
        _input_output_options_group,
        _trim_options_group,
        *[
            {
                "name": "Cluster (Starcode) Options",
                "options": [
                    "--ratio",
                    "--distance",
                ],
            },
            {
                "name": "Quality (Fastp) Options",
                "options": ["--quality", "--unqualified-percent", "--fastp-args"],
            },
            {
                "name": "Filter Options",
                "options": ["--filter-count", "--filter-percent", "--offset"],
            },
        ],
        _general_options_group,
    ],
    "pycashier merge": [
        _input_output_options_group,
        {"name": "Merge (Fastp) Options", "options": ["--fastp-args"]},
        _general_options_group,
    ],
    "pycashier scrna": [
        _input_output_options_group,
        {
            "name": _trim_options_group["name"],
            "options": ["--minimum-length"] + _trim_options_group["options"][:-1],
        },
        _general_options_group,
    ],
    "pycashier combine": [_input_output_options_group, _general_options_group],
}
##########################


# Click Command Configs
##########################


@click.group(
    context_settings=CONTEXT_SETTINGS,
)
@click.version_option(package_name="pycashier", prog_name="pycashier")
def cli():
    """Cash in on DNA Barcode Tags
    \n\n\n
    See `[b cyan]pycashier COMMAND -h[/]` for more information.
    """
    pass


@cli.command()
@click.option(
    "-i",
    "--input",
    help="source directory containing fastq files",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@add_options(
    [
        *_output_options,
        *_general_options,
        *_trim_options,
        *_quality_options,
        *_cluster_options,
        *_filter_options,
    ]
)
@click.pass_context
def extract(
    ctx,
    input,
    output,
    pipeline,
    quality,
    unqualified_percent,
    fastp_args,
    skip_trimming,
    error,
    length,
    upstream_adapter,
    downstream_adapter,
    unlinked_adapters,
    ratio,
    distance,
    filter_percent,
    filter_count,
    offset,
    verbose,
    threads,
    save_config,
):
    """
    extract DNA barcodes from a directory of fastq files
    \n\n\n
    Sample names should be delimited with a ".", such as `[b cyan][yellow]<sample>[/yellow].raw.fastq[/]`,
    anything succeeding the first period will be ignored by `[b cyan]pycashier[/]`.
    \n\n\n
    If your data is paired-end with overlapping barcodes, see `[b cyan]pycashier merge[/]`.
    """

    # validate that filter count and filter percent aren't both defined
    filter = validate_filter_args(ctx)

    if save_config:
        save_params(ctx)

    console.print(("[b]\n[cyan]PYCASHIER:[/cyan] Starting Extraction\n"))
    print_params(ctx)

    fastqs = get_fastqs(input)

    processed_fastqs = sample_check(
        fastqs,
        pipeline,
        output,
        quality,
        ratio,
        distance,
        filter,
        offset,
    )

    fastqs = [f for f in fastqs if f not in processed_fastqs]

    extract_all(
        fastqs,
        output,
        pipeline,
        quality,
        unqualified_percent,
        fastp_args,
        skip_trimming,
        error,
        length,
        upstream_adapter,
        downstream_adapter,
        unlinked_adapters,
        ratio,
        distance,
        filter,
        offset,
        verbose,
        threads,
    )


@cli.command()
@click.option(
    "-i",
    "--input",
    help="source directory containing gzipped R1 and R2 fastq files",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    help="output directory",
    default="./mergedfastqs",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
)
@add_options([_output_options[1], *_general_options])
@click.option(
    "-fa",
    "--fastp-args",
    help="additional arguments provided as a string passed verbatim to fastp",
    type=str,
)
@click.pass_context
def merge(
    ctx,
    input,
    output,
    pipeline,
    fastp_args,
    threads,
    verbose,
    save_config,
):
    """
    merge overlapping paired-end reads using fastp
    \n\n\n
    Simple wrapper over `[b cyan]fastp[/]` to combine R1 and R2 from PE fastq files.
    \n\n\n
    [i]NOTE[/]: fastq files must be gzipped or `[b cyan]pycashier[/]` will exit.
    """

    if save_config:
        save_params(ctx)

    console.print(("[b]\n[cyan]PYCASHIER:[/cyan] Starting Merge\n"))

    print_params(ctx)

    merge_all(
        [f for f in input.iterdir()],
        input,
        pipeline,
        output,
        threads,
        verbose,
        fastp_args,
    )


@cli.command()
@click.option(
    "-i",
    "--input",
    help="source directory containing sam files from scRNA-seq",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "-ml",
    "--minimum-length",
    help="minimum length of extracted barcode",
    default=10,
    show_default=True,
)
@add_options([*_output_options, *_trim_options[:-2], *_general_options])
@click.pass_context
def scrna(
    ctx,
    input,
    output,
    pipeline,
    minimum_length,
    length,
    error,
    upstream_adapter,
    downstream_adapter,
    threads,
    verbose,
    save_config,
):
    """
    extract expressed DNA barcodes from scRNA-seq
    \n\n\n
    Designed for interoperability with 10X scRNA-seq workflow.
    After processing samples with `[b cyan]cellranger[/]` resulting
    bam files should be converted to sam files using `[b cyan]samtools[/]`.
    \n\n\n
    [i]NOTE[/]: You can speed this up by providing a sam file with only
    the unmapped reads.
    """
    if save_config:
        save_params(ctx)

    console.print(("[b]\n[cyan]PYCASHIER:[/cyan] Starting Single Cell Extraction\n"))
    print_params(ctx)
    single_cell(
        input,
        pipeline,
        output,
        error,
        minimum_length,
        length,
        upstream_adapter,
        downstream_adapter,
        threads,
        verbose,
    )


@cli.command()
@click.option(
    "-i",
    "--input",
    help="source directory containing output files from [b cyan]pycashier extract",
    default="outs",
    show_default=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    help="combined tsv of all samples found in input directory",
    default="combined.tsv",
    show_default=True,
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
)
@add_options([*_general_options[2:]])
@click.pass_context
def combine(
    ctx,
    input,
    output,
    save_config,
):
    """
    combine resulting output of [b cyan]extract[/]
    """

    if save_config:
        save_params(ctx)

    combine_outs(input, output)
