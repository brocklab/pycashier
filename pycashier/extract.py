from .cluster import cluster
from .read_filter import read_filter
from .term import term
from .trim import trim


def extract_all(
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
):

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
