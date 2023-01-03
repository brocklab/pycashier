from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import click

from ._checks import pre_run_check
from .config import load_params


def init_check(ctx: click.Context, param: str, check: bool) -> None:
    if not check:
        pre_run_check(command=ctx.to_info_dict()["command"]["name"])


def add_options(
    options: List[Callable],
) -> Callable[[click.decorators.FC], click.decorators.FC]:
    def _add_options(func: click.decorators.FC) -> click.decorators.FC:
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


@dataclass
class Option:
    """custom options class to wrap click.option"""

    param_decls: Sequence[str]
    help: str = ""
    default: Optional[Union[str, int, float, Path]] = None
    show_default: bool = False
    is_flag: bool = False
    type: Any = None
    required: bool = False
    params: Dict[str, Any] = field(default_factory=dict)
    name: str = ""
    category: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            self.name = max(self.param_decls, key=len).lstrip("-")

    def get_click_option(self) -> Callable[[click.decorators.FC], click.decorators.FC]:
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

    # def get_click_option_decorator(self, func: click.decorators.FC) ->click.decorators.FC:
    #     func = self.get_click_option()(func)
    #     return func

    def long(self) -> str:
        """return longest param declaration"""
        return max(self.param_decls, key=len)


general_opts = ("verbose", "config", "save-config")


class OptionMap:
    def __init__(
        self, options: Tuple[Option, ...], subcmd_ref: Dict[str, Tuple[str, ...]]
    ) -> None:
        self.opts = {opt.name: opt for opt in options}
        self.subcmds = {k: [self.opts[opt] for opt in v] for k, v in subcmd_ref.items()}

    def long_by_category(self, category: str) -> Generator[str, None, None]:
        return (opt.long() for opt in self.opts.values() if opt.category == category)


optmap = OptionMap(
    (
        Option(
            ["-o", "--output"],
            help="output directory",
            default="./outs",
            show_default=True,
            type=click.Path(file_okay=False, path_type=Path),
            category="input/output",
        ),
        Option(
            ["-p", "--pipeline"],
            help="pipeline directory",
            default="./pipeline",
            show_default=True,
            type=click.Path(file_okay=False, path_type=Path),
            category="input/output",
        ),
        Option(
            ["-v", "--verbose"],
            help="print the output of underlying software",
            is_flag=True,
            category="general",
        ),
        Option(
            ["-t", "--threads"],
            help="number of cpu cores to use",
            default=1,
            show_default=True,
            category="general",
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
            category="general",
        ),
        Option(
            ["--save-config"],
            help="save current params to file specified by `--config`",
            type=click.Choice(["explicit", "full"], case_sensitive=False),
            category="general",
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
            category="hidden",
        ),
        Option(
            ["-y", "--yes"],
            help="answer yes to prompts",
            is_flag=True,
            category="general",
        ),
        Option(
            ["-e", "--error"],
            help="error tolerance supplied to cutadapt",
            default=0.1,
            show_default=True,
            category="trim",
        ),
        Option(
            ["-l", "--length"],
            help="target length of extracted barcode",
            default=20,
            show_default=True,
            category="trim",
        ),
        Option(
            ["-ua", "--upstream-adapter"],
            help="5' sequence flanking barcode",
            default="ATCTTGTGGAAAGGACGAAACACCG",
            category="trim",
        ),
        Option(
            ["-da", "--downstream-adapter"],
            help="3' sequence flanking barcode",
            default="GTTTTAGAGCTAGAAATAGCAAGTT",
            category="trim",
        ),
        Option(
            ["--unlinked-adapters"],
            help="run cutadapt using unlinked adapters",
            is_flag=True,
            category="trim",
        ),
        Option(
            ["--skip-trimming"],
            help="skip cutadapt trimming entirely and use reads as-is",
            is_flag=True,
            category="trim",
        ),
        Option(
            ["-q", "--quality"],
            help="minimum PHRED quality for filtering reads",
            default=30,
            show_default=True,
            category="quality",
        ),
        Option(
            ["-up", "--unqualified-percent"],
            help="minimum percent of bases which can be below quality threshold",
            default=20,
            show_default=True,
            category="quality",
        ),
        Option(
            ["-fa", "--fastp-args"],
            help="additional arguments provided as a string passed verbatim to fastp",
            type=str,
            category="general",
        ),
        Option(
            ["-r", "--ratio"],
            help="ratio to use for message passing clustering",
            default=3,
            show_default=True,
            category="cluster",
        ),
        Option(
            ["-d", "--distance"],
            help="levenshtein distance for clustering",
            default=1,
            show_default=True,
            type=click.IntRange(1, 8),
            category="cluster",
        ),
        Option(
            ["-fc", "--filter-count"],
            help="minium nominal number of reads",
            type=int,
            category="filter",
        ),
        Option(
            ["-fp", "--filter-percent"],
            help="minimum percentage of total reads",
            default=0.005,
            show_default=True,
            category="filter",
        ),
        Option(
            ["--offset"],
            help="length offset from target barcode length post-clustering",
            default=1,
            show_default=True,
            category="filter",
        ),
        Option(
            ["-s", "--samples"],
            help="comma seperated list of samples to process",
            type=str,
            category="input/output",
        ),
        # make these their own group for clarity?
        # merge options
        Option(
            ["-i", "--input", "input_"],
            help="source directory containing gzipped R1 and R2 fastq files",
            required=True,
            type=click.Path(exists=True, file_okay=False, path_type=Path),
            name="merge-i",
            category="input/output",
        ),
        Option(
            ["-o", "--output"],
            help="output directory",
            default="./mergedfastqs",
            show_default=True,
            type=click.Path(file_okay=False, path_type=Path),
            name="merge-o",
            category="input/output",
        ),
        # extract
        Option(
            ["-i", "--input", "input_"],
            help="source directory containing fastq files",
            required=True,
            type=click.Path(exists=True, file_okay=False, path_type=Path),
            name="extract-i",
            category="input/output",
        ),
        # scrna opts
        Option(
            ["-i", "--input", "input_"],
            help="source directory containing sam files from scRNA-seq",
            required=True,
            type=click.Path(exists=True, file_okay=False, path_type=Path),
            name="scrna-i",
            category="input/output",
        ),
        Option(
            ["-ml", "--minimum-length"],
            help="minimum length of extracted barcode",
            default=10,
            show_default=True,
            category="scrna",
        ),
        Option(
            ["-i", "--input", "input_"],
            help="source directory containing output files from [hl]pycashier extract[/]",
            default="./outs",
            show_default=True,
            type=click.Path(exists=True, file_okay=False, path_type=Path),
            name="combine-i",
            category="input/output",
        ),
        Option(
            ["-o", "--output"],
            help="combined tsv of all samples found in input directory",
            default="./combined.tsv",
            show_default=True,
            type=click.Path(exists=False, dir_okay=False, path_type=Path),
            name="combine-o",
            category="input/output",
        ),
        Option(
            ["--columns"],
            help="comma seperated list of three names for columns",
            default="sample,sequence,count",
            show_default=True,
            category="combine",
        ),
    ),
    {
        "combine": ("combine-i", "samples", "combine-o", "columns", *general_opts),
        "extract": (
            "extract-i",
            "samples",
            "output",
            "pipeline",
            "quality",
            "unqualified-percent",
            "fastp-args",
            "error",
            "length",
            "upstream-adapter",
            "downstream-adapter",
            "unlinked-adapters",
            "skip-trimming",
            "ratio",
            "distance",
            "filter-count",
            "filter-percent",
            "offset",
            "threads",
            "yes",
            *general_opts,
        ),
        "merge": (
            "merge-i",
            "samples",
            "merge-o",
            "pipeline",
            "fastp-args",
            "threads",
            "yes",
            *general_opts,
        ),
        "scrna": (
            "scrna-i",
            "samples",
            "output",
            "pipeline",
            "error",
            "length",
            "upstream-adapter",
            "downstream-adapter",
            "minimum-length",
            "threads",
            "yes",
            *general_opts,
        ),
    },
)
