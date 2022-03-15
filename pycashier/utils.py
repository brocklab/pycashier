import sys

from .console import console


def get_fastqs(src):
    fastqs = [f for f in src.iterdir()]
    if not fastqs:
        console.print(f"Source dir: {src}, appears to be empty...")
        console.print("Exiting.")
        sys.exit(1)

    for f in fastqs:

        if f.suffix != ".fastq":
            print(
                f"ERROR! There is a non fastq file in the provided fastq directory: {f}"
            )
            print("Exiting.")
            sys.exit(1)

    return fastqs


def convert_to_csv(in_file, out_file):

    for i, line in enumerate(in_file):

        if not line.startswith("@") or in_file[i - 1].strip() == "+":
            continue
        seq_id = line.strip()
        sequence = in_file[i + 1].strip()
        out_file.write(f"{seq_id}\t{sequence}\n")


def fastq_to_csv(in_file, out_file):

    with open(in_file) as f_in:
        with open(out_file, "w") as f_out:
            convert_to_csv(f_in.readlines(), f_out)


def extract_csv_column(csv_file, column):

    ext = csv_file.suffix
    tmp_out = csv_file.with_suffix(f".c{column}{ext}")
    with open(csv_file, "r") as csv_in:
        with open(tmp_out, "w") as csv_out:
            for line in csv_in:
                linesplit = line.split("\t")
                csv_out.write(f"{linesplit[column-1]}")

    return tmp_out


def combine_outs(input, output):

    files = {f.name.split(".")[0]: f for f in input.iterdir()}

    console.print(f"Combing output files for {len(files)} samples.")

    with output.open("w") as csv_out:
        csv_out.write("sample\tsequence\tcount\n")
        for sample, f in files.items():
            with f.open("r") as csv_in:
                for line in csv_in:
                    csv_out.write(f"{sample}\t{line}")
