from .term import term
from .utils import extract_csv_column, run_cmd


def cluster(sample, pipeline, ratio, distance, quality, threads, verbose, status):

    extracted_csv = pipeline / f"{sample}.q{quality}.barcodes.tsv"
    output_file = pipeline / f"{sample}.q{quality}.barcodes.r{ratio}d{distance}.tsv"

    if not output_file.is_file():
        if not extracted_csv.with_suffix(".c2.tsv").is_file():
            # ? if this file exists this wont be reached and pycashier won't know what the "input_file" is
            input_file = extract_csv_column(extracted_csv, 2)

        term.process("clustering barcodes w/ [b]starcode[/]")
        command = f"starcode -d {distance} -r {ratio} -t {threads} -i {input_file} -o {output_file}"

        run_cmd(command, sample, output_file, verbose, status)

        input_file.unlink()

        term.process("clustering complete")

    else:

        term.process("skipping clustering")
