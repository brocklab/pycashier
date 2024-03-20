import importlib.util
import sys
from pathlib import Path
from shutil import which
from typing import Dict, List, Optional

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .term import term

PACKAGES = ["cutadapt", "fastp", "starcode", "pysam"]
CMD_PACKAGES: Dict[str, List[str]] = {
    "": PACKAGES,
    "receipt": [],
    "merge": ["fastp"],
    "extract": ["fastp", "cutadapt", "starcode"],
    "scrna": ["pysam", "cutadapt"],
}


def generate_table(command: str, pkg_map: Dict[str, Optional[str]]) -> Table:
    table = Table(box=box.SIMPLE, header_style="bold cyan", collapse_padding=True)
    table.add_column("package", justify="center")
    table.add_column("installed", justify="center")
    table.add_column("path")

    for name, exists in pkg_map.items():
        table.add_row(
            name,
            "[green]yes[/green]" if exists else "[red]no[/red]",
            Text(str(exists if exists else "Not found"), overflow="fold"),
            style="bold" if name in CMD_PACKAGES[command] else "dim",
        )
    return table


def check_file_permissions() -> None:
    try:
        # attempt to trigger PermissionError
        Path("pycashier.toml").is_file()
    except PermissionError:
        term.print(
            "[PycashierPermissionError] reading and writing from current directory not possible",
            err=True,
        )
        term.print(
            "If you are using docker please supply user flag, for example `-u $(id -u):$(id -g)`"
        )
        term.quit()


def pre_run_check(command: str = "", show: bool = False) -> None:
    """Check for runtime dependencies

    Args:
        command: Name of pycashier subcommand.
        show: If true, show table regardless.
    """
    pkg_locs = {name: find_tool(name) for name in PACKAGES}

    if None in pkg_locs.values() or show:
        table = generate_table(command, pkg_locs)

        term.print(
            Panel(
                table,
                title="Dependencies",
            ),
        )
        term.print(f"python exe: [bold]{sys.executable}[/bold]")

        term.print(
            "It's recommended to install pycashier within a conda environment.\n"
            "See the repo for details: [link]https://github.com/brocklab/pycashier[/link]",
        )
        if None in pkg_locs.values():
            term.print(
                f"\n[red bold] FAILED PRE-RUN CHECKS for [hl]pycashier {command}[/hl]!\n",
            )
            term.quit()

    check_file_permissions()


def find_tool(name: str) -> Optional[str]:
    """Check whether `name` is on PATH and marked as executable.

    Args:
        name: Executable/dependency.
    Returns:
        True for success, False otherwise
    """

    if not name == "pysam":
        return which(name)

    spec = importlib.util.find_spec("pysam")
    if spec:
        return spec.origin

    return None
