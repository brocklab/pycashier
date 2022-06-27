import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

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


@dataclass
class Option:
    """custom options class to wrap click.option"""

    param_decls: Optional[Sequence[str]] = None
    help: str = None
    default: str = None
    show_default: bool = False
    is_flag: bool = False
    type: Any = None
    required: bool = False
    params: Dict[str, Any] = field(default_factory=dict)

    def get_click_option(self):
        return click.option(
            *self.param_decls,
            help=self.help,
            default=self.default,
            show_default=self.show_default,
            is_flag=self.is_flag,
            type=self.type,
            required=self.required,
            **self.params,
        )

    def get_click_option_decorator(self, func):
        func = self.get_click_option()(func)
        return func

    def long(self):
        """return longest param declaration"""
        return max(self.param_decls, key=len)


shared_options = {
    "output": [
        Option(
            ["-o", "--output"],
            help="output directory",
            default="./outs",
            show_default=True,
            type=click.Path(file_okay=False, path_type=Path),
        ),
        Option(
            ["-p", "--pipeline"],
            help="pipeline directory",
            default="./pipeline",
            show_default=True,
            type=click.Path(file_okay=False, path_type=Path),
        ),
    ],
    "general": [
        Option(
            ["-v", "--verbose"],
            help="print the output of underlying software",
            is_flag=True,
        ),
        Option(
            ["-t", "--threads"],
            help="number of cpu cores to use",
            default=1,
            show_default=True,
        ),
        Option(
            ["-c", "--config"],
            help="read parameter values from config file",
            show_default=True,
            default=Path("pycashier.toml"),
            type=click.Path(dir_okay=False),
            params=dict(
                expose_value=False,
                is_eager=True,
                callback=load_params,
            ),
        ),
        Option(
            ["--save-config"],
            help="save current params to file specified by `--config`",
            type=click.Choice(["explicit", "full"], case_sensitive=False),
        ),
        Option(
            ["--skip-init-check"],
            help="skip runtime dependency check",
            is_flag=True,
            params=dict(
                hidden=True,
                expose_value=False,
                callback=init_check,
            ),
        ),
    ],
    "trim": [
        Option(
            ["-e", "--error"],
            help="error tolerance supplied to cutadapt",
            default=0.1,
            show_default=True,
        ),
        Option(
            ["-l", "--length"],
            help="target length of extracted barcode",
            default=20,
            show_default=True,
        ),
        Option(
            ["-ua", "--upstream-adapter"],
            help="5' sequence flanking barcode",
            default="ATCTTGTGGAAAGGACGAAACACCG",
        ),
        Option(
            ["-da", "--downstream-adapter"],
            help="3' sequence flanking barcode",
            default="GTTTTAGAGCTAGAAATAGCAAGTT",
        ),
        Option(
            ["--unlinked-adapters"],
            help="run cutadapt using unlinked adapters",
            is_flag=True,
        ),
        Option(
            ["--skip-trimming"],
            help="skip cutadapt trimming entirely and use reads as-is",
            is_flag=True,
        ),
    ],
    "quality": [
        Option(
            ["-q", "--quality"],
            help="minimum PHRED quality for filtering reads",
            default=30,
            show_default=True,
        ),
        Option(
            ["-up", "--unqualified-percent"],
            help="minimum percent of bases which can be below quality threshold",
            default=20,
            show_default=True,
        ),
        Option(
            ["-fa", "--fastp-args"],
            help="additional arguments provided as a string passed verbatim to fastp",
            type=str,
        ),
    ],
    "cluster": [
        Option(
            ["-r", "--ratio"],
            help="ratio to use for message passing clustering",
            default=3,
            show_default=True,
        ),
        Option(
            ["-d", "--distance"],
            help="levenshtein distance for clustering",
            default=1,
            show_default=True,
            type=click.IntRange(1, 8),
        ),
    ],
    "filter": [
        Option(
            ["-fc", "--filter-count"],
            help="minium nominal number of reads",
            type=int,
        ),
        Option(
            ["-fp", "--filter-percent"],
            help="minimum percentage of total reads",
            default=0.005,
            show_default=True,
        ),
        Option(
            ["--offset"],
            help="length offset from target barcode length post-clustering",
            default=1,
            show_default=True,
        ),
    ],
}

options = {
    "merge": [
        Option(
            ["-i", "--input"],
            help="source directory containing gzipped R1 and R2 fastq files",
            required=True,
            type=click.Path(exists=True, file_okay=False, path_type=Path),
        ),
        Option(
            ["-o", "--output"],
            help="output directory",
            default="./mergedfastqs",
            show_default=True,
            type=click.Path(file_okay=False, path_type=Path),
        ),
        shared_options["output"][1],
        *shared_options["general"],
        Option(
            ["-fa", "--fastp-args"],
            help="additional arguments provided as a string passed verbatim to fastp",
            type=str,
        ),
    ],
    "extract": [
        Option(
            ["-i", "--input"],
            help="source directory containing fastq files",
            required=True,
            type=click.Path(exists=True, file_okay=False, path_type=Path),
        ),
        *[opt for opts in shared_options.values() for opt in opts],
    ],
    "scrna": [
        Option(
            ["-i", "--input"],
            help="source directory containing sam files from scRNA-seq",
            required=True,
            type=click.Path(exists=True, file_okay=False, path_type=Path),
        ),
        Option(
            ["-ml", "--minimum-length"],
            help="minimum length of extracted barcode",
            default=10,
            show_default=True,
        ),
        *[
            option
            for option in [
                *shared_options["output"],
                *shared_options["trim"][:-2],
                *shared_options["general"],
            ]
        ],
    ],
    "combine": [
        Option(
            ["-i", "--input"],
            help="source directory containing output files from [b cyan]pycashier extract[/]",
            default="./outs",
            show_default=True,
            type=click.Path(exists=True, file_okay=False, path_type=Path),
        ),
        Option(
            ["-o", "--output"],
            help="combined tsv of all samples found in input directory",
            default="./combined.tsv",
            show_default=True,
            type=click.Path(exists=False, dir_okay=False, path_type=Path),
        ),
        *[option for option in shared_options["general"][2:]],
    ],
}


def get_shared_flags(category, start=0, end=None):
    end = len(shared_options[category]) if end is None else end
    return [option.long() for option in shared_options[category][start:end]]


_help_groups_ref = {
    "Input/Output Options": ["--input", *get_shared_flags("output")],
    "Trim (Cutadapt) Options": ["--minimum-length", *get_shared_flags("trim")],
    "Cluster (Starcode) Options": get_shared_flags("cluster"),
    "Quality (Fastp) Options": get_shared_flags("quality"),
    "Merge (Fastp) Options": ["--fastp-args"],
    "Filter Options": get_shared_flags("filter"),
    "General Options": [*get_shared_flags("general"), "--help"],
    "hidden": ["--skip-init-check"],
}


def get_help_groups(
    options,
    extra_groups=[],
):
    flags = [option.long() for option in options] + ["--help"]
    groups = ["Input/Output Options", *extra_groups, "General Options"]
    help_groups = {group: [] for group in groups}
    for group in groups:
        for flag in flags:
            if flag in _help_groups_ref["hidden"]:
                continue
            if flag in _help_groups_ref[group]:
                help_groups[group].append(flag)

    return help_groups


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


@cli.command(
    option_groups=get_help_groups(
        options["extract"],
        extra_groups=[
            "Quality (Fastp) Options",
            "Trim (Cutadapt) Options",
            "Cluster (Starcode) Options",
            "Filter Options",
        ],
    ),
    help=Pycashier.extract.__doc__,
)
@add_options([option.get_click_option() for option in options["extract"]])
@click.pass_context
def extract(ctx, save_config, **kwargs):
    pycashier = Pycashier(ctx, save_config)
    pycashier.extract(ctx, **kwargs)


@cli.command(
    option_groups=get_help_groups(
        options["merge"],
        extra_groups=[
            "Quality (Fastp) Options",
            "Merge (Fastp) Options",
        ],
    ),
    help=Pycashier.merge.__doc__,
)
@add_options([option.get_click_option() for option in options["merge"]])
@click.pass_context
def merge(ctx, save_config, **kwargs):
    pycashier = Pycashier(ctx, save_config)
    pycashier.merge(**kwargs)


@cli.command(
    option_groups=get_help_groups(
        options["scrna"],
        extra_groups=[
            "Trim (Cutadapt) Options",
        ],
    ),
    help=Pycashier.scrna.__doc__,
)
@add_options([option.get_click_option() for option in options["scrna"]])
@click.pass_context
def scrna(ctx, save_config, **kwargs):
    pycashier = Pycashier(ctx, save_config)
    pycashier.scrna(**kwargs)


@cli.command(
    option_groups=get_help_groups(options["combine"]),
    help=Pycashier.combine.__doc__,
)
@add_options([option.get_click_option() for option in options["combine"]])
@click.pass_context
def combine(ctx, save_config, **kwargs):
    pycashier = Pycashier(ctx, save_config)
    pycashier.combine(**kwargs)


def main():
    cli(prog_name="pycashier")


if __name__ == "__main__":
    main()
