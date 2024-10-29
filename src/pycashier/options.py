from __future__ import annotations

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
)

import click

from ._checks import pre_run_check
from .config import load_params
from .utils import validate_filter_args


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


class Option:
    """custom options class to wrap click.option"""

    def __init__(
        self,
        param_decls: Sequence[str],
        help: str = "",
        default: str | int | float | Path | None = None,
        show_default: bool = False,
        is_flag: bool = False,
        type: Any = None,
        required: bool = False,
        params: Dict[str, Any] = {},
        name: str = "",
        category: Optional[str] = None,
    ):
        self.param_decls = param_decls
        self.help = help
        self.default = default
        self.show_default = show_default
        self.is_flag = is_flag
        self.type = type
        self.required = required
        self.params = params
        self.category = category

        if name:
            self.name = name
        else:
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


general_opts = (
    "verbose",
    "config",
    "save-config",
    "skip-init-check",
    "log-file",
    "pipeline",
    "samples",
)


class OptionMap:
    def __init__(
        self, options: List[Option], subcmd_ref: Dict[str, Tuple[str, ...]]
    ) -> None:
        self.opts = {opt.name: opt for opt in options}
        self.subcmds = {k: [self.opts[opt] for opt in v] for k, v in subcmd_ref.items()}

    def long_by_category(self, category: str) -> Generator[str, None, None]:
        return (opt.long() for opt in self.opts.values() if opt.category == category)

    def get(self, param: str) -> Any:
        """return default value for param"""
        try:
            opt = self.opts[param]
        except KeyError:
            raise ValueError(f"{param} does not exist")
        return opt.default


_duplicate_options_args_kwargs = {
    "fastp-args": (
        ["-fa", "--fastp-args"],
        dict(
            help="additional arguments passed to fastp",
            show_default=True,
        ),
    ),
    "input": (
        ["-i", "--input", "input_"],
        dict(
            required=True,
            type=click.Path(exists=True, file_okay=False, path_type=Path),
            category="input/output",
        ),
    ),
    "output": (
        ["-o", "--output"],
        dict(
            help="output directory",
            show_default=True,
            type=click.Path(file_okay=False, path_type=Path),
            category="input/output",
        ),
    ),
}


def _make_deduplicated_opt(option: str, subcmd: str, **unique_kwargs: Any) -> Option:
    args, kwargs = _duplicate_options_args_kwargs[option]
    kwargs.update(unique_kwargs)
    kwargs.update({"name": f"{option}-{subcmd}"})
    return Option(args, **kwargs)  # type: ignore


_options = [
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
        ["-s", "--samples"],
        help="comma separated list of samples to process",
        type=str,
        category="input/output",
    ),
    Option(
        ["-v", "--verbose"],
        help="show more output, set log level to debug",
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
        is_flag=False,
        params=dict(
            hidden=True,
            expose_value=False,
            callback=init_check,
        ),
        category="hidden",
    ),
    Option(
        ["--log-file"],
        help=r"path to log file [dim]\[default: <pipeline-dir>/pycashier.log]",
        category="general",
        type=click.Path(dir_okay=False, path_type=Path),
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
        default="GTGGAAAGGACGAAACACCG",
        category="trim",
    ),
    Option(
        ["-da", "--downstream-adapter"],
        help="3' sequence flanking barcode",
        default="GTTTTAGAGCTAGAAATAGC",
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
        ["-r", "--ratio"],
        help="ratio to use for message passing clustering",
        default=3.0,
        type=float,
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
        ["-ml", "--minimum-length"],
        help="minimum length of extracted barcode",
        default=10,
        show_default=True,
        category="scrna",
    ),
    Option(
        ["--no-overlap"],
        help="skip per lineage overlap column",
        is_flag=True,
    ),
    Option(
        ["-ca", "--cutadapt-args"],
        help="additional arguments passed to cutadapt",
        type=str,
        default="--max-n=0 -n 2 --trimmed-only",
        show_default=True,
        category="trim",
    ),
]


_options += [
    _make_deduplicated_opt(
        "fastp-args",
        "extract",
        default="--dont_eval_duplication",
        category="quality",
    ),
    _make_deduplicated_opt(
        "fastp-args",
        "merge",
        default="-m -c -G -Q -L",
        category="merge",
    ),
    _make_deduplicated_opt(
        "input",
        "merge",
        help="source directory containing gzipped R1 and R2 fastq files",
    ),
    _make_deduplicated_opt(
        "input",
        "extract",
        help="source directory containing fastq files",
    ),
    _make_deduplicated_opt(
        "input",
        "scrna",
        help="source directory containing sam files from scRNA-seq",
    ),
    _make_deduplicated_opt(
        "input",
        "receipt",
        default="./outs",
        show_default=True,
    ),
    _make_deduplicated_opt(
        "output",
        "merge",
        default="./mergedfastqs",
    ),
    _make_deduplicated_opt(
        "output",
        "receipt",
        help="combined tsv of all samples found in input directory",
        type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
        default="./combined.tsv",
    ),
]
optmap = OptionMap(
    _options,
    {
        "receipt": (
            "input-receipt",
            "output-receipt",
            "no-overlap",
            *general_opts,
        ),
        "extract": (
            "input-extract",
            "output",
            "quality",
            "unqualified-percent",
            "fastp-args-extract",
            "cutadapt-args",
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
            "input-merge",
            "output-merge",
            "fastp-args-merge",
            "threads",
            "yes",
            *general_opts,
        ),
        "scrna": (
            "input-scrna",
            "output",
            "error",
            "length",
            "upstream-adapter",
            "downstream-adapter",
            "cutadapt-args",
            "minimum-length",
            "threads",
            "yes",
            *general_opts,
        ),
    },
)


class PycashierOpts:
    input_: Path
    threads: int
    pipeline: Path
    output: Path
    verbose: bool
    log_file: Path
    samples: Optional[str] = None
    fastp_args: str

    quality = optmap.get("quality")
    unqualified_percent = optmap.get("unqualified-percent")
    error = optmap.get("error")
    length = optmap.get("length")
    distance = optmap.get("distance")
    ratio = optmap.get("ratio")
    upstream_adapter = optmap.get("upstream-adapter")
    downstream_adapter = optmap.get("downstream-adapter")
    minimum_length = optmap.get("minimum-length")
    unlinked_adapters = optmap.get("unlinked-adapters")
    skip_trimming = optmap.get("skip-trimming")
    offset = optmap.get("offset")
    cutadapt_args = optmap.get("cutadapt-args")
    filter_count = optmap.get("filter-count")
    filter_percent = optmap.get("filter-percent")
    no_overlap = optmap.get("no-overlap")
    yes = optmap.get("yes")

    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)
        if self.log_file is None:
            self.log_file = self.pipeline / "pycashier.log"

    def update_filter(self, ctx: click.Context) -> None:
        filter = validate_filter_args(ctx)
        self.filter_percent = filter.get("filter_percent")
        self.filter_count = filter.get("filter_count")
