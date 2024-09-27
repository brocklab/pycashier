#!/usr/bin/env python3

import os
import shlex
import subprocess
from pathlib import Path
from textwrap import indent

ROOT = Path(__file__).parent.parent


def run(cmd, **kwargs):
    return subprocess.run(shlex.split(cmd), **kwargs)


def get_output(cmd, **kwargs):
    return subprocess.check_output(shlex.split(cmd), text=True, **kwargs)


COMMAND_RST_TMPL = """
pycashier {command}
----------------------------------


.. tab:: image

  .. image:: svgs/{image_name}

.. tab:: plaintext

  .. code-block::

{code}
"""


# TODO: add yartsu to docs dependencies?
def make_svg(command, image_path):
    run(f"viv run yartsu -- -o {image_path} -- pycashier {command} -h")


# make the pycashier plaintext not limited to 80 columns
env = os.environ.copy()
env["COLUMNS"] = "110"


def generate_rst(command=""):
    image_path = (
        ROOT
        / "docs/svgs"
        / (f"pycashier-{command}.svg" if command else "pycashier.svg")
    )
    make_svg(command, image_path)
    help_output = get_output(f"pycashier {command} -h", env=env)
    return COMMAND_RST_TMPL.format(
        command=command, image_name=image_path.name, code=indent(help_output, "      ")
    )


def main():
    cli_docs = "\n".join(
        ["=============", "CLI Reference", "=============", generate_rst()]
        + [generate_rst(cmd) for cmd in ["extract", "merge", "receipt", "scrna"]]
    )
    (ROOT / "docs/cli.rst").write_text(cli_docs)


if __name__ == "__main__":
    main()
