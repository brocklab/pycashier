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

        print()
        term.print(f"──────────────── {sample} ───────────────────", style="dim")

        with term.status(
            f"Processing sample: [green]{sample}[/green]", spinner="dots12"
        ):

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
            )

            cluster(sample, pipeline, ratio, distance, quality, threads, verbose)

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

        term.print(f"[green]{sample}[/green]: processing completed")

    term.print("\n[green]FINISHED!")
