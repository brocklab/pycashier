from rich.console import Console

MAX_WIDTH = 110

console = Console()

if console.width > MAX_WIDTH:
    console.width = MAX_WIDTH
