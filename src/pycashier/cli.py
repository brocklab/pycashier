import shutil
from typing import Any, Callable, Dict, List

import click
from click_rich_help import StyledGroup
from rich.traceback import install

from ._checks import pre_run_check
from .options import Option, optmap
from .pycashier import Pycashier
from .term import theme

install(suppress=[click], show_locals=True)


def add_options(
    options: List[Callable],
) -> Callable[[click.decorators.FC], click.decorators.FC]:
    def _add_options(func: click.decorators.FC) -> click.decorators.FC:
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


_help_groups_ref = {
    k: set(v)
    for k, v in {
        "Input/Output Options": ["--input", *optmap.long_by_category("input/output")],
        "Trim (Cutadapt) Options": [
            "--minimum-length",
            *optmap.long_by_category("trim"),
        ],
        "Cluster (Starcode) Options": optmap.long_by_category("cluster"),
        "Quality (Fastp) Options": optmap.long_by_category("quality"),
        "Merge Options": optmap.long_by_category("merge"),
        "Filter Options": optmap.long_by_category("filter"),
        "Receipt Options": ["--no-overlap"],
        "General Options": [
            *optmap.long_by_category("general"),
            "--help",
        ],
        "hidden": ["--skip-init-check"],
    }.items()
}


def get_help_groups(
    options: List[Option],
    extra_groups: List[str] = [],
) -> Dict[str, List[str]]:
    flags = [option.long() for option in options] + ["--help"]
    groups = ["Input/Output Options", *extra_groups, "General Options"]
    help_groups: Dict[str, List[str]] = {group: [] for group in groups}
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
    theme=theme,
    context_settings=CONTEXT_SETTINGS,
)
@click.version_option(package_name="pycashier", prog_name="pycashier")
def cli() -> None:
    """Cash in on DNA Barcode Tags
    \n\n\n
    See `[hl]pycashier COMMAND -h[/]` for more information.
    """
    pass


@cli.command(
    option_groups=get_help_groups(
        optmap.subcmds["extract"],
        extra_groups=[
            "Quality (Fastp) Options",
            "Trim (Cutadapt) Options",
            "Cluster (Starcode) Options",
            "Filter Options",
        ],
    ),
    help=Pycashier.extract.__doc__,
)
@add_options([option.get_click_option() for option in optmap.subcmds["extract"]])
@click.pass_context
def extract(ctx: click.Context, save_config: bool, **kwargs: Any) -> None:
    pycashier = Pycashier(ctx, save_config, **kwargs)
    pycashier.extract(ctx, **kwargs)


@cli.command(
    option_groups=get_help_groups(
        optmap.subcmds["merge"], extra_groups=["Merge Options"]
    ),
    help=Pycashier.merge.__doc__,
)
@add_options([option.get_click_option() for option in optmap.subcmds["merge"]])
@click.pass_context
def merge(ctx: click.Context, save_config: bool, **kwargs: Any) -> None:
    pycashier = Pycashier(ctx, save_config, **kwargs)
    pycashier.merge()


@cli.command(
    option_groups=get_help_groups(
        optmap.subcmds["scrna"],
        extra_groups=[
            "Trim (Cutadapt) Options",
        ],
    ),
    help=Pycashier.scrna.__doc__,
)
@add_options([option.get_click_option() for option in optmap.subcmds["scrna"]])
@click.pass_context
def scrna(ctx: click.Context, save_config: bool, **kwargs: Any) -> None:
    pycashier = Pycashier(ctx, save_config, **kwargs)
    pycashier.scrna()


@cli.command(
    option_groups=get_help_groups(
        optmap.subcmds["receipt"], extra_groups=["Receipt Options"]
    ),
    help=Pycashier.receipt.__doc__,
)
@add_options([option.get_click_option() for option in optmap.subcmds["receipt"]])
@click.pass_context
def receipt(ctx: click.Context, save_config: bool, **kwargs: Any) -> None:
    pycashier = Pycashier(ctx, save_config, **kwargs)
    pycashier.receipt()


@cli.command(hidden=True, help="perform check for pycashier dependencies")
def checks() -> None:
    pre_run_check(show=True)


def main() -> None:
    cli(prog_name="pycashier")


if __name__ == "__main__":
    main()
