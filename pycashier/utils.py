import csv
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import click
import tomlkit
from rich.status import Status

from .term import term


def get_fastqs(src: Path) -> List[Path]:
    """determine fastq files
    Args:
        src: Input directory that contains fastq files.
    Returns:
        List of fastq files (may be gzipped).
    """

    fastqs = [f for f in src.iterdir() if not f.name.startswith(".")]
    if not fastqs:
        term.print(f"Source dir: {src}, appears to be empty...")
        term.print("Exiting.")
        sys.exit(1)

    for f in fastqs:

        if not any(f.name.endswith(suffix) for suffix in [".fastq", ".fastq.gz"]):
            term.print(
                f"[InputError]: There is a non fastq file in the provided fastq directory: {f}",
                err=True,
            )
            term.print("Exiting.")
            sys.exit(1)

    return fastqs


def fastq_to_tsv(in_file: Path, out_file: Path) -> None:
    """convert fastq file to tsv

    Args:
        in_file: Fastq file to convert.
        out_file: TSV file to write to.
    """

    with open(in_file) as f_in:
        with open(out_file, "w") as f_out:
            lines = f_in.readlines()
            for i, line in enumerate(lines):

                if not line.startswith("@") or lines[i - 1].strip() == "+":
                    continue
                seq_id = line.strip()
                sequence = lines[i + 1].strip()
                f_out.write(f"{seq_id}\t{sequence}\n")


def extract_csv_column(csv_file: Path, column: int) -> Path:
    """get column from csv file

    Args:
        csv_file: File to extract column from.
        column: Column to extract.
    Return:
        File containg only the extracted column.
    """
    ext = csv_file.suffix
    tmp_out = csv_file.with_suffix(f".c{column}{ext}")
    with open(csv_file, "r") as csv_in:
        with open(tmp_out, "w") as csv_out:
            for line in csv_in:
                linesplit = line.split("\t")
                csv_out.write(f"{linesplit[column-1]}")

    return tmp_out


def get_filter_count(file_in: Path, filter_percent: float) -> int:
    """calculate filter cutoff

    Args:
        file_in: Clustered lineage counts to filter.
        filter_percent: Percent cutoff of total reads count.
    Returns:
        Minimum nominal cutoff value.
    """
    total_reads = 0.0

    with open(file_in, newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="\t")
        for row in spamreader:
            total_reads += float(row[1])

    return int(round(total_reads * filter_percent / 100, 0))


def combine_outs(input_dir: Path, output: Path) -> None:
    """combine output tsvs into one file

    Args:
        input_dir: Directory containing csv files to combine.
        output: TSV to save all data to.
    """
    files = {f.name.split(".")[0]: f for f in input_dir.iterdir()}

    term.print(f"Combing output files for {len(files)} samples.")

    with output.open("w") as tsv_out:
        # TODO: make columns configurable?
        tsv_out.write("sample\tsequence\tcount\n")
        for sample, f in files.items():
            with f.open("r") as tsv_in:
                for line in tsv_in:
                    tsv_out.write(f"{sample}\t{line}")


def validate_filter_args(ctx: click.Context) -> Dict[str, float]:
    """validate filter argument from config and CLI

    Args:
        ctx: Click context.
    Returns:
        Dictionary defining the filter type and value.
    """
    if ctx.params["filter_count"] or ctx.params["filter_count"] == 0:
        if ctx.get_parameter_source("filter_percent").value == 3:  # type: ignore
            ctx.params["filter_percent"] = None
            del ctx.params["filter_percent"]
            return {"filter_count": ctx.params["filter_count"]}
        else:
            raise click.BadParameter(
                "`--filter-count` and `--filter-percent` are mutually exclusive"
            )
    else:
        del ctx.params["filter_count"]
        return {"filter_percent": ctx.params["filter_percent"]}


def save_params(ctx: click.Context) -> None:
    """save parameters to config file

    Args:
        ctx: Click context.
    """
    cmd = ctx.info_name
    params = {k: v for k, v in ctx.params.items() if v}
    save_type = params.pop("save_config")

    try:
        config_file = Path(ctx.obj["config_file"])
    except TypeError:
        raise click.BadParameter("use `--save-config` with a specified `--config`")

    if config_file.is_file():
        term.print(f"Updating current config file at [hl]{config_file}")
        with config_file.open("r") as f:
            config = tomlkit.load(f)
    else:
        term.print(f"Staring a config file at [hl]{config_file}")
        config = tomlkit.document()

    if save_type == "explicit":
        params = {k: v for k, v in params.items() if ctx.get_parameter_source(k).value != 3}  # type: ignore

    # sanitize the path's for writing to toml
    for k in ["input", "pipeline", "output"]:
        if k in params.keys():
            params[k] = str(params[k])

    config[cmd] = params  # type: ignore

    null_hints = {"extract": ["filter_count", "fastp_args"], "merge": ["fastp_args"]}
    if cmd in null_hints.keys() and save_type == "full":
        for param in null_hints[cmd]:  # type: ignore
            if param not in params.keys():
                config[cmd].add(tomlkit.comment(f"{param} ="))  # type: ignore

    with config_file.open("w") as f:
        f.write(tomlkit.dumps(config))

    term.print("Exiting...")
    ctx.exit()


def load_params(ctx: click.Context, param: str, filename: Path) -> None:
    """load parameters from config file

    Args:
        ctx: Click context.
        param: Invoked command and config table head.
        filename: Config filename.
    """

    if not filename or ctx.resilient_parsing:
        return

    ctx.default_map = {}
    if Path(filename).is_file():
        with Path(filename).open("r") as f:
            params = tomlkit.load(f)
        if params:
            ctx.default_map = params.get(ctx.info_name, {})
    elif Path(filename) != Path("pycashier.toml"):
        term.print(
            f"[InputError]: Specified config file ({filename}) does not exist.",
            err=True,
        )
        sys.exit(1)

    ctx.obj = {"config_file": filename}


def exit_status(p: subprocess.CompletedProcess, file: Path) -> bool:
    """check command exit status and file size

    Args:
        p: Completed subprocess
        file: File to check for nonzero size.
    Returns:
        True for success, False otherwise.
    """
    return True if p.returncode != 0 or file.stat().st_size == 0 else False


def run_cmd(
    command: str, sample: str, output: Path, verbose: bool, status: Status
) -> None:
    """run a subcommand

    Args:
        command: Subcommand to be run in subprocess.
        sample: Name of sample.
        output: Directory of immediate output.
        verbose: If true, print subcommand output.
        status: Status to pause if writing to stderr printing needed.
    """
    cmd_name = command.split()[0]

    p = subprocess.run(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    # remove 'progress: ##%' output from starcode
    stdout = (
        p.stdout
        if not cmd_name == "starcode"
        else "\n".join(
            [line for line in p.stdout.splitlines() if not line.startswith("progress")]
        )
    )

    if verbose or exit_status(p, output):
        term.subcommand(sample, cmd_name, command, stdout)

    if exit_status(p, output):
        status.stop()
        term.print(
            f"[{cmd_name.capitalize()}Error]: Failed to extract reads for sample: [green]{sample}[/green]\n"
            f"see above for {cmd_name} output",
            err=True,
        )
        sys.exit(1)


def confirm_samples(samples: List[str], yes: bool) -> None:
    """display and confirm samples

    Args:
        samples: List of samples for confirmation.
        yes: True if --yes flag used at runtime.
    """

    term.print(f"[hl]Samples[/]: {', '.join(sorted(samples))}\n")
    if not yes and not term.confirm("Continue with these samples?"):
        sys.exit()
    if not yes:
        term.print()


def check_output(file: Path, message: str) -> bool:
    """check for output file and print message

    Args:
        file: Resulting file of step.
        message: Text to display related to step.
    Returns:
        True for success, False otherwise.
    """

    if not file.is_file():
        term.process(message)
        return True
    else:
        term.process(message, status="skip")
        return False
