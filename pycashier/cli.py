import shutil
from pathlib import Path

import click
from click_rich_help import StyledGroup

from ._checks import pre_run_check
from .pycashier import Pycashier
from .utils import load_params


def init_check(ctx, param, check):
    if not check:
        pre_run_check()


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


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


_general_option_group = {
    "General Options": [
        "--help",
        "--verbose",
        "--threads",
        "--config",
        "--save-config",
    ],
}

_input_output_option_group = {
    "Input/Output Options": ["--input", "--output", "--pipeline"],
}
_trim_option_group = {
    "Trim (Cutadapt) Options": [
        "--error",
        "--length",
        "--upstream-adapter",
        "--downstream-adapter",
        "--unlinked-adapters",
        "--skip-trimming",
    ],
}
_extract_option_groups = {
    **_input_output_option_group,
    **_trim_option_group,
    **{
        "Cluster (Starcode) Options": [
            "--ratio",
            "--distance",
        ],
        "Quality (Fastp) Options": [
            "--quality",
            "--unqualified-percent",
            "--fastp-args",
        ],
        "Filter Options": ["--filter-count", "--filter-percent", "--offset"],
    },
    **_general_option_group,
}


CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"],
    max_content_width=shutil.get_terminal_size(fallback=(110, 24))[0],
)


@click.group(
    cls=StyledGroup,
    context_settings=CONTEXT_SETTINGS,
)
@click.version_option(package_name="pycashier", prog_name="pycashier")
def cli():
    """Cash in on DNA Barcode Tags
    \n\n\n
    See `[b cyan]pycashier COMMAND -h[/]` for more information.
    """
    pass


@cli.command(option_groups=_extract_option_groups, help=Pycashier.extract.__doc__)
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
def extract(ctx, save_config, **kwargs):
    pycashier = Pycashier(ctx, save_config)
    pycashier.extract(ctx, **kwargs)


@cli.command(
    option_groups={
        **_input_output_option_group,
        **{"Merge (Fastp) Options": ["--fastp-args"]},
        **_general_option_group,
    },
    help=Pycashier.merge.__doc__,
)
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
def merge(ctx, save_config, **kwargs):
    print(kwargs)
    pycashier = Pycashier(ctx, save_config)
    pycashier.merge(ctx, **kwargs)


@cli.command(
    option_groups={
        **_input_output_option_group,
        **{
            "Trim (Cutadapt) Options": ["--minimum-length"]
            + _trim_option_group["Trim (Cutadapt) Options"][:-2]
        },
        **_general_option_group,
    },
    help=Pycashier.scrna.__doc__,
)
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
def scrna(ctx, save_config, **kwargs):
    pycashier = Pycashier(ctx, save_config)
    pycashier.scrna(ctx, **kwargs)


@cli.command(
    option_groups={
        "Input/Output Options": ["--input", "--output"],
        "General Options": ["--help", "--config", "--save-config"],
    },
    help=Pycashier.combine.__doc__,
)
@click.option(
    "-i",
    "--input",
    help="source directory containing output files from [b cyan]pycashier extract[/]",
    default="./outs",
    show_default=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    help="combined tsv of all samples found in input directory",
    default="./combined.tsv",
    show_default=True,
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
)
@add_options([*_general_options[2:]])
@click.pass_context
def combine(ctx, save_config, **kwargs):
    pycashier = Pycashier(ctx, save_config)
    pycashier.combine(ctx, **kwargs)


def main():
    cli(prog_name="pycashier")


if __name__ == "__main__":
    main()
