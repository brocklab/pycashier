from .extract import extract_all
from .merge import merge_all
from .single_cell import single_cell
from .term import console
from .termui import print_params, sample_check
from .utils import combine_outs, get_fastqs, save_params, validate_filter_args


class Pycashier:
    def __init__(self, ctx, save_config):
        if save_config:
            save_params(ctx)

        print_params(ctx)

    def extract(
        self,
        ctx,
        input,
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
        offset,
        verbose,
        threads,
        **kwargs,
    ):
        """
        extract DNA barcodes from a directory of fastq files

        \b
        Sample names should be delimited with a ".", such as `[b cyan][yellow]<sample>[/yellow].raw.fastq[/]`,
        anything succeeding the first period will be ignored by `[b cyan]pycashier[/]`.

        If your data is paired-end with overlapping barcodes, see `[b cyan]pycashier merge[/]`.
        """

        # validate that filter count and filter percent aren't both defined
        filter = validate_filter_args(ctx)

        console.print(("[b]\n[cyan]PYCASHIER:[/cyan] Starting Extraction\n"))

        fastqs = get_fastqs(input)

        processed_fastqs = sample_check(
            fastqs,
            pipeline,
            output,
            quality,
            ratio,
            distance,
            filter,
            offset,
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
        input,
        output,
        pipeline,
        fastp_args,
        threads,
        verbose,
    ):
        """
        merge overlapping paired-end reads using fastp
        \n\n\n
        Simple wrapper over `[b cyan]fastp[/]` to combine R1 and R2 from PE fastq files.
        \n\n\n
        """

        console.print(("[b]\n[cyan]PYCASHIER:[/cyan] Starting Merge\n"))

        merge_all(
            [f for f in input.iterdir()],
            input,
            pipeline,
            output,
            threads,
            verbose,
            fastp_args,
        )

    def scrna(
        self,
        input,
        output,
        pipeline,
        minimum_length,
        length,
        error,
        upstream_adapter,
        downstream_adapter,
        threads,
        verbose,
    ):
        """
        extract expressed DNA barcodes from scRNA-seq
        \n
        \b
        Designed for interoperability with 10X scRNA-seq workflow.
        After processing samples with `[b cyan]cellranger[/]` resulting
        bam files should be converted to sam files using `[b cyan]samtools[/]`.
        \n
        [i]NOTE[/]: You can speed this up by providing a sam file with only
        the unmapped reads.
        """
        console.print(
            ("[b]\n[cyan]PYCASHIER:[/cyan] Starting Single Cell Extraction\n")
        )

        single_cell(
            input,
            pipeline,
            output,
            error,
            minimum_length,
            length,
            upstream_adapter,
            downstream_adapter,
            threads,
            verbose,
        )

    def combine(
        self,
        input,
        output,
    ):
        """
        combine resulting output of [b cyan]extract[/]
        """

        combine_outs(input, output)
