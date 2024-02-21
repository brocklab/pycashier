import filecmp
import shutil
from pathlib import Path
from typing import Any, Tuple

from click import BaseCommand
from click.testing import CliRunner, Result


def click_run(cli: BaseCommand, *args: Any, **kwargs: Any) -> Result:
    runner = CliRunner()
    return runner.invoke(cli, *args, **kwargs)


def purge(*paths: Path) -> None:
    for p in paths:
        if p.is_dir():
            shutil.rmtree(p)
        elif p.is_file():
            p.unlink()


def cmp_outs(filename: str, paths: Tuple[Path, Path]) -> bool:
    file_one, file_two = (filepath / filename for filepath in paths)
    return filecmp.cmp(file_one, file_two)
