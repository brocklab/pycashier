import sys
from shutil import which
from typing import Dict, List

from rich import box
from rich.panel import Panel
from rich.table import Table

from .term import term

PACKAGES = ["cutadapt", "fastp", "starcode", "pysam"]
CMD_PACKAGES: Dict[str, List[str]] = {
    "combine": [],
    "merge": ["fastp"],
    "extract": ["fastp", "cutadapt", "starcode"],
    "scrna": ["pysam", "cutadapt"],
}


def yes_no(condition: bool) -> str:
    """colored yes/no output for table

    Args:
        condition: bool
    Returns:
        Formatted boolean text.
    """

    return "[green]yes[/green]" if condition else "[red]no[/red]"


def pre_run_check(command: str) -> None:
    """Check for runtime dependencies

    Args:
        command: Name of pycashier subcommand.
    """
    pkgs_exist = {name: is_tool(name) for name in PACKAGES}
    if False in pkgs_exist.values():

        table = Table(box=box.SIMPLE, header_style="bold cyan", collapse_padding=True)
        table.add_column("package", justify="center")
        table.add_column("installed", justify="center")
        table.add_column("needed")

        for name, exists in pkgs_exist.items():
            table.add_row(
                name,
                yes_no(exists),
                yes_no(name in CMD_PACKAGES[command]),
                style="bold" if not exists and name in CMD_PACKAGES[command] else "dim",
            )

        term.print(
            f"\n[red bold] FAILED PRE-RUN CHECKS for [hl]pycashier {command}[/hl]!!\n",
            Panel.fit(
                table,
                title="Dependencies",
            ),
            "It's recommended to install pycashier within a conda environment.\n"
            "See the repo for details: [link]https://github.com/brocklab/pycashier[/link]",
        )
        sys.exit(1)


def is_tool(name: str) -> bool:
    """Check whether `name` is on PATH and marked as executable.

    Args:
        name: Executable/dependency.
    Returns:
        True for success, False otherwise
    """
    if name == "pysam":
        try:
            # replace with importlib?
            import pysam  # noqa

            return True
        except ImportError:
            return False
    return which(name) is not None
