import sys
from shutil import which

import rich_click as click
from rich import box
from rich.panel import Panel
from rich.table import Table

from .console import console

PACKAGES = ["cutadapt", "fastp", "pysam", "starcode"]


def pre_run_check():

    pkgs_exist = {name: is_tool(name) for name in PACKAGES}
    if False in pkgs_exist.values():
        console.print("\n[red bold] FAILED PRE-RUN CHECKS!!\n")

        table = Table(box=box.SIMPLE, header_style="bold cyan", collapse_padding=True)

        table.add_column("package", justify="right")
        table.add_column("found?", justify="left")
        for name, exists in pkgs_exist.items():
            if exists:
                found = "[green] yes"
            else:
                found = "[red] no"
            table.add_row(name, found)

        console.print(
            Panel.fit(
                table,
                border_style=click.rich_click.STYLE_COMMANDS_PANEL_BORDER,
                title="Dependencies",
                title_align=click.rich_click.ALIGN_COMMANDS_PANEL,
                width=click.rich_click.MAX_WIDTH,
            )
        )

        console.print(
            "It's recommended to install pycashier within a conda environment."
        )
        console.print(
            "See README on github for details: [link]https://github.com/brocklab/pycashier[/link]"
        )
        sys.exit(1)


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    if name == "pysam":
        try:
            import pysam  # noqa

            return True
        except ImportError:
            return False
    return which(name) is not None
