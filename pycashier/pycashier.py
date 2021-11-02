import sys
from pathlib import Path

from .cli import get_args, sample_check
from .cluster import cluster
from .console import console
from .extract import extract
from .merge import merge
from .read_filter import read_filter
from .single_cell import single_cell


def main():

    cli_args = get_args()

    console.rule()
    console.rule("Barcode Extraction with CASHIER")
    console.rule()

    sourcedir = Path(cli_args["main"]["sourcedir"])

    fastqs = [f for f in sourcedir.iterdir()]

    if not fastqs:
        console.log(f"Source dir: {sourcedir}, appears to be empty...")
        console.log("Exiting.")
        sys.exit(1)

    Path(cli_args["main"]["pipelinedir"]).mkdir(exist_ok=True)
    Path(cli_args["main"]["outdir"]).mkdir(exist_ok=True)

    if cli_args["single_cell"]:

        single_cell(sourcedir, cli_args)

    if cli_args["merge"]["merge"]:

        merge(fastqs, sourcedir, cli_args)

    for f in fastqs:

        ext = f.suffix

        if ext != ".fastq":
            print(
                f"ERROR! There is a non fastq file in the provided fastq directory: {f}"
            )
            print("Exiting.")
            sys.exit(1)

    processed_samples = sample_check(sourcedir, fastqs, cli_args)

    for fastq in fastqs:

        sample = fastq.name.split(".")[0]

        if sample in processed_samples:
            console.log(f"Skipping Processing for [green]{sample}[/green]")
            console.rule()
            continue

        with console.status(
            f"Processing sample: [green]{sample}[/green]", spinner="dots12"
        ):

            extract(sample, fastq, **cli_args["main"], **cli_args["extract"])

            cluster(sample, **cli_args["main"], **cli_args["cluster"])

            read_filter(
                sample,
                **cli_args["main"],
                **cli_args["filter"],
                **cli_args["cluster"],
            )

        console.log(f"[green]{sample}[/green]: processing completed")
        console.rule()

    console.print("\n[green]FINISHED!")


if __name__ == "__main__":
    main()
