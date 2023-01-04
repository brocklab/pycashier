from pathlib import Path
from typing import Any, Dict

import click

from .config import save_params
from .extract import extract_all
from .merge import merge_all
from .single_cell import single_cell
from .term import term
from .termui import print_params, sample_check
from .utils import combine_outs, get_input_files, validate_filter_args


class Pycashier:
    def __init__(self, ctx: click.Context, save_config: bool) -> None:
        if save_config:
            save_params(ctx)
        print_params(ctx)

    def extract(
        self,
        ctx: click.Context,
        input_: Path,
        samples: str,
        output: Path,
        pipeline: Path,
        quality: int,
        unqualified_percent: float,
        fastp_args: Dict[str, str],
        skip_trimming: bool,
        error: float,
        length: int,
        upstream_adapter: str,
        downstream_adapter: str,
        unlinked_adapters: bool,
        ratio: int,
        distance: int,
        offset: int,
        verbose: bool,
        threads: int,
        yes: bool,
        **kwargs: Any,
    ) -> None:
        """
        extract DNA barcodes from a directory of fastq files

        \b
        Sample names should be delimited with a ".", such as `[hl][yellow]<sample>[/yellow].raw.fastq[/]`,
        anything succeeding the first period will be ignored by `[hl]pycashier[/]`.

        If your data is paired-end with overlapping barcodes, see `[hl]pycashier merge[/]`.
        """

        # validate that filter count and filter percent aren't both defined
        filter = validate_filter_args(ctx)

        term.print(("[b]\n[cyan]PYCASHIER:[/cyan] Starting Extraction\n"))

        fastqs = get_input_files(
            input_,
            samples.split(",") if samples else None,
            exts=[".fastq", ".fastq.gz"],
        )

        processed_fastqs = sample_check(
            fastqs,
            pipeline,
            output,
            quality,
            ratio,
            distance,
            filter,
            offset,
            yes,
        )

        fastqs = [f for f in fastqs if f not in processed_fastqs]

        extract_all(
            fastqs,
            output,
            pipeline,
            quality,
            unqualified_percent,
            fastp_args,
            skip_trimming,
            error,
            length,
            upstream_adapter,
            downstream_adapter,
            unlinked_adapters,
            ratio,
            distance,
            filter,
            offset,
            verbose,
            threads,
        )

    def merge(
        self,
        input_: Path,
        samples: str,
        output: Path,
        pipeline: Path,
        fastp_args: Dict[str, str],
        threads: int,
        verbose: bool,
        yes: bool,
    ) -> None:
        """
        merge overlapping paired-end reads using fastp
        \n\n\n
        Simple wrapper over `[hl]fastp[/]` to combine R1 and R2 from PE fastq files.
        \n\n\n
        """

        term.print(("[b]\n[cyan]PYCASHIER:[/cyan] Starting Merge\n"))

        merge_all(
            get_input_files(
                input_,
                samples.split(",") if samples else None,
                exts=[".fastq", ".fastq.gz"],
            ),
            pipeline,
            output,
            threads,
            verbose,
            fastp_args,
            yes,
        )

    def scrna(
        self,
        input_: Path,
        samples: str,
        output: Path,
        pipeline: Path,
        minimum_length: int,
        length: int,
        error: float,
        upstream_adapter: str,
        downstream_adapter: str,
        threads: int,
        verbose: bool,
        yes: bool,
    ) -> None:
        """
        extract expressed DNA barcodes from scRNA-seq
        \n
        \b
        Designed for interoperability with 10X scRNA-seq workflow.
        After processing samples with `[hl]cellranger[/]` resulting
        bam files should be converted to sam files using `[hl]samtools[/]`.
        \n
        [i]NOTE[/]: You can speed this up by providing a sam file with only
        the unmapped reads.
        """
        term.print(("[b]\n[cyan]PYCASHIER:[/cyan] Starting Single Cell Extraction\n"))

        single_cell(
            input_,
            samples.split(",") if samples else None,
            pipeline,
            output,
            error,
            minimum_length,
            length,
            upstream_adapter,
            downstream_adapter,
            threads,
            verbose,
            yes,
        )

    def combine(
        self,
        input_: Path,
        samples: str,
        output: Path,
        columns: str,
        verbose: bool,
    ) -> None:
        """
        combine resulting output of [hl]extract[/]
        """

        combine_outs(
            input_, samples.split(",") if samples else None, output, columns.split(",")
        )
