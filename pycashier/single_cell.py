import sys
from pathlib import Path
from typing import List

from rich.status import Status

try:
    import pysam
except ImportError:
    pass

from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

from .term import term
from .utils import check_output, confirm_samples, get_input_files, run_cmd


def sam_to_name_labeled_fastq(
    sample: str, sam_file: Path, out_file: Path, status: Status
) -> None:
    """convert sam file to metadata labeled fastq

    Args:
        sample: Name of sample.
        sam_file: Sam file to convert.
        out_file: Converted fastq file.
        status: Rich.console status to suspend for stderr printing.
    """
    sam_file

    # if the file is a sam file this is the only way I can find in the pysam API to get the total number of reads
    # we really only need this for the progess bar though
    with pysam.AlignmentFile(
        str(sam_file.absolute()), "r", check_sq=False, check_header=False  # type: ignore
    ) as sam:
        sam_length = sam.count()

    # we don't care about indicies or genomes. since cutadapt will do the heavy lifting here
    with open(out_file, "w") as f_out, pysam.AlignmentFile(
        str(sam_file.absolute()), "r", check_sq=False, check_header=False  # type: ignore
    ) as sam:
        status.stop()
        with Progress(
            SpinnerColumn("pipe", style="line"),
            *Progress.get_default_columns(),
            "Elapsed:",
            TimeElapsedColumn(),
            transient=True,
            console=term._console,
        ) as progress:
            task = progress.add_task("[red]sam -> fastq", total=sam_length)

            for record in sam.fetch(until_eof=True):

                tagdict = dict(record.tags)
                cell_barcode = None
                if "CB" in tagdict.keys():
                    cell_barcode = tagdict["CB"].split("-")[0]
                elif "CR" in tagdict.keys():
                    cell_barcode = tagdict["CR"]

                umi = None
                if "UB" in tagdict.keys():
                    umi = tagdict["UB"]
                elif "UR" in tagdict.keys():
                    umi = tagdict["UR"]

                if cell_barcode and umi:

                    qualities = record.query_qualities
                    ascii_qualities = "".join([chr(q + 33) for q in qualities])

                    f_out.write(f"@{record.query_name}_{umi}_{cell_barcode}\n")
                    f_out.write(f"{record.query_sequence}\n+\n{ascii_qualities}\n")

                progress.advance(task)

    status.start()


# TODO: use grouper util function?
def labeled_fastq_to_tsv(in_file: Path, out_file: Path) -> None:
    """convert labeled fastq to tsv

    Args:
        in_file: Fastq to convert to tsv.
        out_file: Converted tsv file.
    """

    with open(in_file) as f_in, open(out_file, "w") as f_out:
        read_lines = []
        # TODO: add progress bar
        for line in f_in.readlines():
            read_lines.append(line)
            if len(read_lines) == 4:

                read_name, umi, cell_barcode = read_lines[0].rstrip("\n").split("_")
                lineage_barcode = read_lines[1].rstrip("\n")

                f_out.write(f"{read_name}\t{umi}\t{cell_barcode}\t{lineage_barcode}\n")
                read_lines = []


def single_cell_process(
    sample: str,
    samfile: Path,
    pipeline: Path,
    output: Path,
    error: float,
    minimum_length: int,
    length: int,
    upstream_adapter: str,
    downstream_adapter: str,
    threads: int,
    verbose: bool,
    status: Status,
) -> None:
    """extract barcodes from single cell data

    Args:

        sample: Name of the sample.
        samfile: Path to sam file.
        pipeline: Directory for all intermediary files.
        output: Directory for final tsv files.
        error: Error rate used by cutadapt.
        minimum_length: Minimum barcode length.
        length: Expected lenth of barcode.
        upstream_adapter: 5' barcode flanking sequence.
        downstream_adapter: 3' barcode flanking sequence.
        ratio: Clustering ratio for starcode.
        threads: Number of threads for starcode to use.
        verbose: If true, show subcommand output.
        status: Rich.console status to suspend for stderr printing.
    """

    adapter_string = f"-g {upstream_adapter} -a {downstream_adapter}"
    fastq, barcode_fastq = (
        pipeline / f"{sample}.cell_record_labeled.{ext}"
        for ext in ("fastq", "barcode.fastq")
    )
    tsv_out = output / f"{sample}.cell_record_labeled.barcode.tsv"

    if check_output(fastq, "converting sam to labeled fastq"):
        sam_to_name_labeled_fastq(sample, samfile, fastq, status)

    if check_output(barcode_fastq, "extracting barcodes w/ [b]cutadapt[/]"):

        command = (
            "cutadapt "
            f"-e {error} "
            f"-j {threads} "
            f"--minimum-length={minimum_length} "
            f"--maximum-length={length} "
            "--max-n=0 "
            f"--trimmed-only {adapter_string} "
            "-n 2 "
            f"-o {barcode_fastq} {fastq}"
        )

        run_cmd(command, sample, barcode_fastq, verbose, status)

    if check_output(tsv_out, "converting labeled fastq to tsv"):
        labeled_fastq_to_tsv(barcode_fastq, tsv_out)


def single_cell(
    input_: Path,
    samples: List[str] | None,
    pipeline: Path,
    output: Path,
    error: float,
    minimum_length: int,
    length: int,
    upstream_adapter: str,
    downstream_adapter: str,
    threads: int,
    verbose: bool,
    yes: bool,
) -> None:
    """extract barcodes from set of single cell samples

    Args:

        input_: Directory of sam files.
        samples: List of samples.
        pipeline: Directory for all intermediary files.
        output: Directory for final tsv files.
        error: Error rate used by cutadapt.
        minimum_length: Minimum barcode length.
        length: Expected lenth of barcode.
        upstream_adapter: 5' barcode flanking sequence.
        downstream_adapter: 3' barcode flanking sequence.
        threads: Number of threads for starcode to use.
        verbose: If true, show subcommand output.
        yes: If true, skip sample confirmation.
    """

    # TODO: refactor get_fastq to take a list of extensions and peform this
    for d in [pipeline, output]:
        d.mkdir(exist_ok=True)

    candidate_samfiles = [f for f in input_.iterdir() if not f.name.startswith(".")]
    for f in candidate_samfiles:

        if f.suffix != ".sam":
            term.print(
                f"[ScrnaError]: There is a non sam file in the provided input_ directory: {f}",
                err=True,
            )
            sys.exit(1)
    # TODO: remove this weird type change to dict
    samfiles = get_input_files(input_, samples, [".sam"])
    samfiles_dict = {f.name.split(".")[0]: f for f in samfiles}

    confirm_samples(list(samfiles_dict), yes)

    for sample, samfile in samfiles_dict.items():

        term.process(f"[hl]{sample}[/]", status="start")

        with term.cash_in() as status:

            single_cell_process(
                sample,
                samfile,
                pipeline,
                output,
                error,
                minimum_length,
                length,
                upstream_adapter,
                downstream_adapter,
                threads,
                verbose,
                status,
            )

        term.process(status="end")

    term.print("\n[green]FINISHED!")
    sys.exit()
