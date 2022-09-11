from .term import term
from .utils import check_output, extract_csv_column, run_cmd


def cluster(sample, pipeline, ratio, distance, quality, threads, verbose, status):

    extracted_csv = pipeline / f"{sample}.q{quality}.barcodes.tsv"
    clustered = pipeline / f"{sample}.q{quality}.barcodes.r{ratio}d{distance}.tsv"

    if check_output(
        clustered,
        "clustering barcodes w/ [b]starcode[/]",
    ):

        if not extracted_csv.with_suffix(".c2.tsv").is_file():
            # ? if this file exists this wont be reached and pycashier won't know what the "input_file" is
            input_file = extract_csv_column(extracted_csv, 2)

        command = f"starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {clustered}"

        run_cmd(command, sample, clustered, verbose, status)

        input_file.unlink()

        term.process("clustering complete")
