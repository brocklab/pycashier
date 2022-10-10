from pathlib import Path
from typing import Dict, List, Mapping, Union

from .cluster import cluster
from .read_filter import read_filter
from .term import term
from .trim import trim


def extract_all(
    fastqs: List[Path],
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
    filter: Mapping[str, Union[int, float]],
    offset: int,
    verbose: bool,
    threads: int,
) -> None:
    """peform quality filtering, extraction, clustering, and final filtering

    Args:
        fastqs: List of fastq files.
        output: Directory for final tsv files.
        pipeline: Directory for all intermediary files.
        quality: PHred quality cutoff for filenames.
        unqualified_percent: Percent of bases that may fall below quality cutoff.
        fastp_args: Extra arguments passed to fastp.
        skip_trimming: Skip fastp adapter trimming step.
        error: Error rate used by cutadapt.
        length: Expected lenth of barcode.
        upstream_adapter: 5' barcode flanking sequence.
        downstream_adapter: 3' barcode flanking sequence.
        unlinked_adapters: If true use unlinked_adapters with cutadapt.
        ratio: Clustering ratio for starcode.
        distance: Levenstein distance for starcode.
        filter: Dictionary defining how to filter final clustered barcodes.
        offset: Acceptable insertion or deletion from expected length in final sequences.
        verbose: If true, show subcommand output.
        threads: Number of threads for starcode to use.
    """

    for d in [pipeline, output]:
        d.mkdir(exist_ok=True)

    for fastq in sorted(fastqs):

        sample = fastq.name.split(".")[0]

        term.process(f"[hl]{sample}[/]", status="start")

        with term.cash_in() as status:

            trim(
                sample,
                pipeline,
                fastq,
                quality,
                unqualified_percent,
                fastp_args,
                error,
                threads,
                length,
                distance,
                upstream_adapter,
                downstream_adapter,
                unlinked_adapters,
                skip_trimming,
                verbose,
                status,
            )

            cluster(
                sample, pipeline, ratio, distance, quality, threads, verbose, status
            )

            read_filter(
                sample,
                pipeline,
                output,
                length,
                offset,
                filter,
                quality,
                ratio,
                distance,
            )

        term.process(status="end")

    term.print("\n[green]FINISHED!")
