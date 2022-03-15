from .cluster import cluster
from .console import console
from .read_filter import read_filter
from .trim import trim


def extract_all(
    fastqs,
    output,
    pipeline,
    error,
    length,
    upstream_adapter,
    downstream_adapter,
    unlinked_adapters,
    quality,
    unqualified_percent,
    ratio,
    distance,
    filter,
    offset,
    verbose,
    threads,
):
    print()

    for d in [pipeline, output]:
        d.mkdir(exist_ok=True)

    for fastq in fastqs:

        sample = fastq.name.split(".")[0]

        with console.status(
            f"Processing sample: [green]{sample}[/green]", spinner="dots12"
        ):

            trim(
                sample,
                pipeline,
                fastq,
                error,
                threads,
                length,
                distance,
                upstream_adapter,
                downstream_adapter,
                unlinked_adapters,
                quality,
                unqualified_percent,
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
        console.rule()

    console.print("\n[green]FINISHED!")
