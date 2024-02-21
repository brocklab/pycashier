from __future__ import annotations

import logging
import shutil
import sys
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from textwrap import dedent
from typing import Any, Generator, Optional

from rich.console import Console
from rich.highlighter import NullHighlighter, RegexHighlighter
from rich.logging import RichHandler
from rich.panel import Panel
from rich.prompt import Confirm
from rich.status import Status
from rich.text import Text
from rich.theme import Theme

MAX_WIDTH = 110

theme = Theme(
    {
        "hl": "bold cyan",
        "line": "bright_magenta",
        "border": "red",
        # click-rich-help defaults
        "header": "bold italic cyan",
        "option": "bold yellow",
        "metavar": "green",
        "default": "dim",
        "required": "dim red",
    },
    inherit=True,
)


class StreamFormatter(logging.Formatter):
    """Rich-enabled logging formatter"""

    def __init__(self, verbose: bool) -> None:
        super().__init__()
        self.FORMATS = {
            **{
                level: (f"[{color}]%(levelname)-7s[/]" " %(message)s")
                for level, color in {
                    logging.DEBUG: "dim",
                    logging.WARNING: "yellow",
                    logging.ERROR: "red",
                    logging.CRITICAL: "red",  # not used
                }.items()
            },
            logging.INFO: "%(message)s",
        }
        if verbose:
            self.FORMATS.update({logging.INFO: "[text]%(levelname)-7s[/] %(message)s"})

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = MutlilineFormatter(log_fmt)
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    """strip rich markdown from log messages"""

    def format(self, record: logging.LogRecord) -> str:
        formatter = MutlilineFormatter(self._fmt)
        record.msg = Text.from_ansi(Text.from_markup(record.msg).plain).plain
        return formatter.format(record)


class MutlilineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        outlines = []
        lines = (save_msg := record.msg).splitlines()
        for line in lines:
            record.msg = line
            outlines.append(super().format(record))
        record.msg = save_msg
        record.message = (output := "\n".join(outlines))
        return output


class ErrorHighlighter(RegexHighlighter):
    """Apply style to anything that looks like an error."""

    highlights = [r"(?P<error>\[\w+Error\])"]


class Term:
    """rich-based ui"""

    _status_name: str | None = None
    _status: Status | None = None

    def __init__(self, width: Optional[int] = None) -> None:
        self._process_msg = "default msg"
        self._console = Console(highlight=False, theme=theme, width=width)
        self._err_console = Console(
            theme=Theme({"hl": "bold cyan", "error": "bold red"}, inherit=True),
            stderr=True,
            highlighter=ErrorHighlighter(),
            width=width,
        )

    # use property ?
    def set_logger(self, log_file: Path, verbose: bool) -> None:
        if not (parent := log_file.parent).is_dir():
            term.print(
                f"[CliError] [code]{parent}[/] directory for log file does not exist. "
                f"Please create [code]{parent}[/] first.",
                err=True,
            )
            sys.exit(1)

        logger = logging.getLogger("pycashier")
        logger.setLevel(logging.DEBUG)

        ch = RichHandler(
            console=self._console,
            show_time=False,
            highlighter=NullHighlighter(),
            markup=True,
            show_level=False,
            show_path=False,
        )
        ch.setLevel(logging.INFO if not verbose else logging.DEBUG)
        ch.setFormatter(StreamFormatter(verbose))

        fh = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(FileFormatter("%(asctime)s | %(levelname)8s | %(message)s"))

        logger.addHandler(ch)
        logger.addHandler(fh)
        self.log = logging.getLogger("pycashier")

    @contextmanager
    def _no_status(self) -> Generator[None, None, None]:
        try:
            if status := getattr(self, "_status", None):
                status.stop()
            yield
        finally:
            if status:
                status.start()

    def print(self, *args: Any, err: bool = False, **kwargs: Any) -> None:
        console = self._err_console if err else self._console
        with self._no_status():
            console.print(*args, **kwargs)

    def quit(self, code: int = 1) -> None:
        if status := getattr(self, "_status", None):
            status.stop()
        self._err_console.print("Exiting.")
        sys.exit(code)

    @contextmanager
    def cash_in(self, name: str) -> Generator[Status, None, None]:
        try:
            self._status_name = name
            self._status = self._console.status(
                name, spinner="point", spinner_style="bright_magenta"
            )
            self._status.start()
            yield self._status
        finally:
            if self._status:
                self._status.stop()
            self._status_name = None
            self._status = None

    def mode(self, cmd: str) -> None:
        term.log.info(f"[bold]pycashier [green]{cmd}")

    def confirm(self, *args: Any, **kwargs: Any) -> bool:
        return Confirm.ask(*args, console=self._console, **kwargs)

    def style_title(self, title: str) -> Text:
        return Text.from_markup(f"[reset][hl]{title}[/hl][/reset]")

    def textbox(self, text: str, title: str = "", *args: Any, **kwargs: Any) -> None:
        self.print(
            Panel.fit(
                Text(dedent(text), *args, *kwargs),
                title=self.style_title(title),
                title_align="left",
            )
        )

    @contextmanager
    def process(self, msg: str = "") -> Generator[None, None, None]:
        name = getattr(self, "_status_name")
        status = getattr(self, "_status")
        if msg:
            msg = " [dim]" + msg
        try:
            status.update(name + msg)
            yield
        finally:
            status.update(name)


cols = shutil.get_terminal_size().columns
term = Term(width=MAX_WIDTH if cols > MAX_WIDTH else cols)
