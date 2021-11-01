import argparse
import re
import sys
from pathlib import Path

from rich import box
from rich.prompt import Confirm
from rich.table import Table

from .console import console
from .read_filter import get_filter_count


def get_args():
    parser = argparse.ArgumentParser(
        prog="pycashier",
        usage="%(prog)s [-h] sourcedir"
        #       formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "sourcedir", help="directory containing sam/fastq files to process"
    )
    parser.add_argument(
        "-t",
        "--threads",
        help="number of cpu cores to use (default: %(default)s)",
        metavar="",
        default=1,
    )
    parser.add_argument(
        "-sc",
        "--single_cell",
        help="turn unampped sam files into cell barcode & umi labeled tsv",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="show output of command line calls",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        help="output directory (default: %(default)s)",
        metavar="",
        default="outs",
    )
    parser.add_argument(
        "-pd",
        "--pipelinedir",
        help="directory containing pipeline \
            output files (default: %(default)s)",
        metavar="",
        default="pipeline",
    )

    # extract specific parameters
    extract_parser = parser.add_argument_group(title="extract options")

    extract_parser.add_argument(
        "-e",
        "--error",
        help="error tolerance supplied to cutadapt (default: %(default)s)",
        metavar="",
        default=0.1,
        type=float,
    )
    extract_parser.add_argument(
        "-bl",
        "--barcode_length",
        help="integer length of expected barcode (default: %(default)s)",
        metavar="",
        type=int,
        default=20,
    )
    extract_parser.add_argument(
        "-mbl",
        "--min_barcode_length",
        help="minimum length of expected barcode (default: %(default)s)",
        metavar="",
        type=int,
        default=20,
    )
    extract_parser.add_argument(
        "-ua",
        "--upstream_adapter",
        help="5' sequence flanking barcode",
        metavar="",
        type=str,
        default="ATCTTGTGGAAAGGACGAAACACCG",
    )
    extract_parser.add_argument(
        "-da",
        "--downstream_adapter",
        help="3' sequence flanking barcode region",
        metavar="",
        type=str,
        default="GTTTTAGAGCTAGAAATAGCAAGTT",
    )
    extract_parser.add_argument(
        "-ul",
        "--unlinked_adapters",
        help="run cutadapt using unlinked adapters",
        action="store_true",
    )
    extract_parser.add_argument(
        "-q",
        "--quality",
        help="minimum PHRED quality to use to \
            filter reads (default: %(default)s)",
        metavar="",
        default=30,
        type=int,
    )

    cluster_parser = parser.add_argument_group(title="cluster options")
    cluster_parser.add_argument(
        "-r",
        "--ratio",
        help="ratio to use for message passing clustering (default: %(default)s)",
        metavar="",
        default=3,
        type=int,
    )
    cluster_parser.add_argument(
        "-d",
        "--distance",
        help="levenshtein distance for clustering (default: %(default)s)",
        metavar="",
        default=1,
        type=int,
    )

    filter_parser = parser.add_argument_group("filter_options")
    filter_parser.add_argument(
        "-fc",
        "--filter_count",
        help="nominal number of reads for sequence to pass filter",
        metavar="",
        default=None,
        type=int,
    )
    filter_parser.add_argument(
        "-fp",
        "--filter_percent",
        help="minimum percentage of total reads for sequence to pass filter",
        metavar="",
        default=0.005,
        type=float,
    )

    merge_parser = parser.add_argument_group(title="merge options")
    merge_parser.add_argument(
        "-m",
        "--merge",
        help="merge R1 and R2 fastq files using pear",
        action="store_true",
    )
    merge_parser.add_argument(
        "-ko",
        "--keep_output",
        help="keep auxiliary files output by pear in mergefastqs directory",
        action="store_true",
    )
    merge_parser.add_argument(
        "-pa",
        "--pear_args",
        help="additional arguments to pass to pear",
        metavar="",
        type=str,
        default="",
    )

    args = parser.parse_args()

    return {
        "main": {
            "sourcedir": args.sourcedir,
            "threads": args.threads,
            "quality": args.quality,
            "verbose": args.verbose,
            "outdir": args.outdir,
            "pipelinedir": args.pipelinedir,
        },
        "extract": {
            "error_rate": args.error,
            "upstream_adapter": args.upstream_adapter,
            "downstream_adapter": args.downstream_adapter,
            "barcode_length": args.barcode_length,
            "min_barcode_length": args.min_barcode_length,
            "unlinked_adapters": args.unlinked_adapters,
        },
        "cluster": {
            "ratio": args.ratio,
            "distance": args.distance,
        },
        "merge": {
            "merge": args.merge,
            "keep_output": args.keep_output,
            "pear_args": args.pear_args,
        },
        "filter": {
            "filter_percent": args.filter_percent,
            "filter_count": args.filter_count,
        },
        "single_cell": args.single_cell,
    }


def make_sample_check_table(samples, args):
    processed_samples = []
    table = Table(
        title="[yellow]Samples Queued For Processing",
        box=box.HORIZONTALS,
        header_style="bold bright_blue",
        min_width=80,
    )
    table.add_column(
        "Sample",
        justify="center",
        style="green",
        no_wrap=True,
    )
    table.add_column(
        f"Read Quality\n(Phred Score)\n {args['quality']} ", justify="center"
    )
    table.add_column(
        f"Clustering\n(ratio, distance)\n {args['ratio']}, {args['distance']}",
        justify="center",
    )
    if args["filter_count"] is not None:
        table.add_column(
            f"Filter Cutoff\n(min reads)\n {args['filter_count']}", justify="center"
        )
    else:
        table.add_column(
            f"Filter Cutoff\n(min %)\n {args['filter_percent']} %", justify="center"
        )
    table.add_column("Processed?", justify="center")

    for sample in samples:
        row, processed = check_pipeline_outs(sample, args)

        if processed:
            processed_samples.append(sample)

        table.add_row(*row)

    console.print(table, justify="center")

    print()

    return processed_samples


def check_pipeline_outs(sample, args):
    pipeline = Path(args["pipelinedir"])
    row_list = [sample]

    p1 = re.compile(
        fr'{sample}\.barcodes\.q{args["quality"]}.\
            r{args["ratio"]}d{args["distance"]}\.tsv'
    )
    p2 = re.compile(fr'{sample}\.barcodes\.q{args["quality"]}\.tsv')
    p3 = re.compile(
        fr'{sample}\.barcodes\.q{args["quality"]}.\
            r{args["ratio"]}d{args["distance"]}\.min(?P<filter_count>\d+)\.tsv'
    )

    filters = []
    for f in pipeline.iterdir():
        m = p1.search(f.name)

        if m:
            row_list += ["[bold green]\u2713"] * 2

            filters = []
            for f2 in sorted([f.name for f in Path(args["outdir"]).iterdir()]):
                m = p3.search(f2)
                if m:
                    if args["filter_count"] is not None:
                        filter_count_check = args["filter_count"]
                    else:
                        filter_count_check = get_filter_count(f, args["filter_percent"])

                    if str(filter_count_check) == m.group("filter_count"):
                        filters.append(f"[green]{m.group('filter_count')}[/green]")
                    else:
                        filters.append(m.group("filter_count"))

            if filters:
                row_list.append(", ".join(filters))

            break

    if row_list == [sample]:
        for f in pipeline.iterdir():
            m = p2.search(f.name)
            if m:
                row_list += [":heavy_check_mark:"]

    row_list.extend(["[yellow]Queued"] * (4 - len(row_list)))

    if r"[green]" in "".join(filters):
        row_list.append("[bold green]\u2713")
        processed = True
    else:
        row_list.append("[bold red] Incomplete")
        processed = False

    return row_list, processed


def sample_check(sourcedir, fastqs, cli_args):

    args = {
        "quality": cli_args["main"]["quality"],
        "ratio": cli_args["cluster"]["ratio"],
        "distance": cli_args["cluster"]["distance"],
        "filter_percent": cli_args["filter"]["filter_percent"],
        "filter_count": cli_args["filter"]["filter_count"],
        "pipelinedir": cli_args["main"]["pipelinedir"],
        "outdir": cli_args["main"]["outdir"],
    }

    samples = [f.name.split(".")[0] for f in fastqs]
    # outs_files = sorted([f.name for f in Path(args['outdir']).iterdir()])
    # check_outs(samples, outs_files)\
    processed_samples = make_sample_check_table(samples, args)

    if not Confirm.ask("Continue with these samples?"):
        sys.exit()

    return processed_samples


####################################################
#  functions to get additional samples found in outs
####################################################

# def get_params(f):
#     p = re.compile(
#         r'(?P<sample>\w+)\.barcodes\.q(?P<quality>\d\d).r(?P<ratio>\d+)d(?P<distance>\d+)\.min(?P<filter_count>\d+)\.tsv'
#     )
#     m = p.search(f)
#     if m:
#         return m.groupdict()
#     else:
#         raise ValueError(f"Unexpected file in outs directory:{f}")

# def check_outs(samples, files):
#     table_rows = []

#     for f in files:
#         params = get_params(f)
#         if params['sample'] not in samples:
#             table_rows.append([
#                 params['sample'], params['quality'],
#                 f"{params['ratio']}, {params['distance']}",
#                 params['filter_count']
#             ])
#     if table_rows:
#         console = Console()
#         table = Table(title="Additional Samples Found in Outs Directory",
#                       box=box.HORIZONTALS,
#                       header_style="bold bright_blue",
#                       min_width=70)
#         table.add_column("Sample",
#                          justify="center",
#                          style="green",
#                          no_wrap=True)
#         table.add_column("Read Quality\n(Phred Score)", justify="center")
#         table.add_column('Clustering\n(ratio,distance)', justify='center')
#         table.add_column('Filter Cutoff\n(min reads)', justify='center')
#         for row in table_rows:
#             table.add_row(*row)
#         console.print(table)
