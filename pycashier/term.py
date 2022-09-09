import shutil

from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.prompt import Confirm
from rich.theme import Theme

MAX_WIDTH = 110


class ErrorHighlighter(RegexHighlighter):
    """Apply style to anything that looks like an error."""

    highlights = [r"(?P<error>\[\w+Error\])"]


class Term:
    """rich-based ui"""

    def __init__(self, width=None):
        self._console = Console(highlight=False, width=width)
        self._err_console = Console(
            theme=Theme({"error": "bold red"}, inherit=True),
            stderr=True,
            highlighter=ErrorHighlighter(),
            width=width,
        )

    def print(self, *args, err=False, **kwargs):
        console = self._err_console if err else self._console
        console.print(*args, **kwargs)

    def status(self, *args, **kwargs):
        return self._console.status(*args, **kwargs)

    def confirm(self, *args, **kwargs):
        return Confirm.ask(*args, console=self.console, **kwargs)


cols = shutil.get_terminal_size().columns
term = Term(width=MAX_WIDTH if cols > MAX_WIDTH else cols)
