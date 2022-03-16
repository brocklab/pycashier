from .cluster import cluster
from .console import console
from .read_filter import read_filter
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
        console.print(f"──────────────── {sample} ───────────────────", style="dim")

        with console.status(
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

        console.print(f"[green]{sample}[/green]: processing completed")

    console.print("\n[green]FINISHED!")
