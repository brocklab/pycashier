import shutil
from textwrap import dedent
from typing import Any, Optional

from rich.console import Console
from rich.highlighter import RegexHighlighter
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


class ErrorHighlighter(RegexHighlighter):
    """Apply style to anything that looks like an error."""

    highlights = [r"(?P<error>\[\w+Error\])"]


class Term:
    """rich-based ui"""

    def __init__(self, width: Optional[int] = None) -> None:
        self._console = Console(highlight=False, theme=theme, width=width)
        self._err_console = Console(
            theme=Theme({"hl": "bold cyan", "error": "bold red"}, inherit=True),
            stderr=True,
            highlighter=ErrorHighlighter(),
            width=width,
        )

    def print(self, *args: Any, err: bool = False, **kwargs: Any) -> None:
        console = self._err_console if err else self._console
        console.print(*args, **kwargs)

    def cash_in(self) -> Status:
        return self._console.status(
            "cashing in...", spinner="pipe", spinner_style="bright_magenta"
        )

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

    def subcommand(self, sample: str, pkg: str, command: str, output: str) -> None:
        """print subcommand results"""

        self.print()
        self.textbox(command, title=f"{pkg.upper()} COMMAND | [green]{sample}[/green]")
        self.textbox(output, title=f"{pkg.upper()} OUTPUT | [green]{sample}[/green]")

    def process(self, text: str = "", status: str = "") -> None:
        if status == "start":
            self.print(f"[line]╭── [/]\[{text}]")
        elif status == "end":
            self.print("[line]╰────> [/][green]:heavy_check_mark:[/]")
        elif status == "skip":
            self.print(f"[line]├ [/][dim strike]{Text.from_markup(text)}[/] skipped")
        else:
            self.print(f"[line]├ [/]{text}")


cols = shutil.get_terminal_size().columns
term = Term(width=MAX_WIDTH if cols > MAX_WIDTH else cols)
