import shutil
from typing import Any, Callable, Dict, List

import click
from click_rich_help import StyledGroup

from ._checks import pre_run_check
from .options import Option, optmap
from .pycashier import Pycashier
from .term import theme


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
        "Filter Options": optmap.long_by_category("filter"),
        "Combine Options": ["--columns"],
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
    pycashier = Pycashier(ctx, save_config)
    pycashier.extract(ctx, **kwargs)


@cli.command(
    option_groups=get_help_groups(
        optmap.subcmds["merge"],
    ),
    help=Pycashier.merge.__doc__,
)
@add_options([option.get_click_option() for option in optmap.subcmds["merge"]])
@click.pass_context
def merge(ctx: click.Context, save_config: bool, **kwargs: Any) -> None:
    pycashier = Pycashier(ctx, save_config)
    pycashier.merge(**kwargs)


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
    pycashier = Pycashier(ctx, save_config)
    pycashier.scrna(**kwargs)


@cli.command(
    option_groups=get_help_groups(
        optmap.subcmds["combine"], extra_groups=["Combine Options"]
    ),
    help=Pycashier.combine.__doc__,
)
@add_options([option.get_click_option() for option in optmap.subcmds["combine"]])
@click.pass_context
def combine(ctx: click.Context, save_config: bool, **kwargs: Any) -> None:
    pycashier = Pycashier(ctx, save_config)
    pycashier.combine(**kwargs)


def main() -> None:
    cli(prog_name="pycashier")


if __name__ == "__main__":
    main()
