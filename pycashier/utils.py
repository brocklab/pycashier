import csv
import shlex
import subprocess
import sys
from collections.abc import Iterable
from itertools import zip_longest
from pathlib import Path
from typing import Any, Dict, List

import click
from rich.status import Status

from .term import term


def filter_input_by_sample(
    candidate_files: List[Path], samples: List[str]
) -> List[Path]:
    """filter candidate fastqs based on user provided samples
    Args:
        candidate_fastqs: all fastq files found in input direcotry
        samples: user provided list of samples
    Returns:
        returns list of accepted fastqs
    """

    found, files, ignored = [], [], []
    for f in candidate_files:
        name, *_ = f.name.split(".")
        if name in samples:
            found.append(name)
            files.append(f)
        else:
            ignored.append(name)

    not_found = set(samples).difference(found)
    if not_found:
        term.print(f"[InputError]: Unknown sample(s) -> {not_found}", err=True)
        sys.exit(1)

    if ignored:
        term.print(f"[dim]ignoring {len(set(ignored))} samples")

    return files


def get_input_files(
    src: Path,
    samples: List[str] | None,
    exts: List[str],
) -> List[Path]:
    """determine input files
    Args:
        src: Input directory that contains fastq/sam files.
        samples: List of allowed samples.
        exts: Acceptable file extensions.

    Returns:
        List of fastq/sam files (may be gzipped).
    """

    candidate_files = [f for f in src.iterdir() if not f.name.startswith(".")]

    if not candidate_files:
        term.print(f"[InputError]: Source dir: {src}, appears to be empty...", err=True)
        term.print("Exiting.", err=True)
        sys.exit(1)

    for f in candidate_files:
        if not any(f.name.endswith(suffix) for suffix in exts):
            term.print(
                f"[InputError]: There is a non {exts} file in the provided input directory: {f}",
                err=True,
            )
            term.print("Exiting.")
            sys.exit(1)
        if f.is_symlink() and not f.exists():
            term.print(
                f"[InputError]: There is a symlink in the provided input directory: {f} \n"
                "If using docker: Ensure that symlinks are resolved within the mounted volume "
                "in '/data' or pycashier within docker won't find them.",
                err=True,
            )
            term.print("Exiting.")
            sys.exit(1)

    files = (
        filter_input_by_sample(candidate_files, samples) if samples else candidate_files
    )
    return files


def grouper(iterable: Iterable, n: int) -> "zip_longest[Any]":
    """Collect data into non-overlapping fixed-length chunks or blocks

    adds '_' as placeholder to fill iterable as necessary
    """
    args = [iter(iterable)] * n

    return zip_longest(*args, fillvalue="_")


def fastq_to_tsv(in_file: Path, out_file: Path) -> None:
    """convert fastq file to tsv

    Args:
        in_file: Fastq file to convert.
        out_file: TSV file to write to.
    """
    warn = False
    with open(in_file) as f_in, open(out_file, "w") as f_out:
        for read in grouper(
            f_in,
            4,
        ):
            if "_" in read:
                warn = True
            seq_id, sequence = read[0].strip(), read[1].strip()
            f_out.write(f"{seq_id}\t{sequence}\n")

    if warn:
        term.print("some of the read data was incomplete")
        term.print("verify {in_file.name} was not corrupted")


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
    with open(csv_file, "r") as csv_in, open(tmp_out, "w") as csv_out:
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


def combine_outs(
    input_dir: Path, samples: List[str] | None, output: Path, columns: List[str]
) -> None:
    """combine output tsvs into one file

    Args:
        input_dir: Directory containing csv files to combine.
        samples: list of sample names to use
        output: TSV to save all data to.
        columns: list of column names
    """
    if len(columns) != 3:
        term.print(
            f"[InputError]: Expected three comma seperated column names. \n  Recieved -> {columns}",
            err=True,
        )
        sys.exit(1)

    files = {
        f.name.split(".")[0]: f
        for f in get_input_files(input_dir, samples, exts=[".tsv"])
    }
    term.print(f"Combing output files for {len(files)} samples.")

    with output.open("w") as tsv_out:
        tsv_out.write("\t".join(columns) + "\n")
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
        output: file of immediate output.
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
