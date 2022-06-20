import csv
import sys
from pathlib import Path

import click
import tomlkit

from .term import console


def get_fastqs(src):
    fastqs = [f for f in src.iterdir()]
    if not fastqs:
        console.print(f"Source dir: {src}, appears to be empty...")
        console.print("Exiting.")
        sys.exit(1)

    for f in fastqs:

        if not any(f.name.endswith(suffix) for suffix in [".fastq", ".fastq.gz"]):
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


def get_filter_count(file_in, filter_percent):
    total_reads = 0

    with open(file_in, newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter="\t")
        for row in spamreader:
            total_reads += float(row[1])

    filter_count = int(round(total_reads * filter_percent / 100, 0))

    return filter_count


def validate_filter_args(ctx):
    if ctx.params["filter_count"] or ctx.params["filter_count"] == 0:
        if ctx.get_parameter_source("filter_percent").value == 3:
            ctx.params["filter_percent"] = None
            del ctx.params["filter_percent"]
            return {"filter_count": ctx.params["filter_count"]}
        else:
            raise click.BadParameter(
                "`--filter-count` and `--filter-percent` are mutually exclusive"
            )
    else:
        del ctx.params["filter_count"]
        return {"filter_percent": ctx.params["filter_percent"]}


def save_params(ctx):
    cmd = ctx.info_name
    params = {k: v for k, v in ctx.params.items() if v}
    save_type = params.pop("save_config")

    try:
        config_file = Path(ctx.obj["config_file"])
    except TypeError:
        raise click.BadParameter("use `--save-config` with a specified `--config`")

    if config_file.is_file():
        console.print(f"Updating current config file at [b cyan]{config_file}")
        with config_file.open("r") as f:
            config = tomlkit.load(f)
    else:
        console.print(f"Staring a config file at [b cyan]{config_file}")
        config = tomlkit.document()

    if save_type == "explicit":
        params = {
            k: v for k, v in params.items() if ctx.get_parameter_source(k).value != 3
        }

    # sanitize the path's for writing to toml
    for k in ["input", "pipeline", "output"]:
        if k in params.keys():
            params[k] = str(params[k])

    config[cmd] = params

    null_hints = {"extract": ["filter_count", "fastp_args"], "merge": ["fastp_args"]}
    if cmd in null_hints.keys() and save_type == "full":
        for param in null_hints[cmd]:
            if param not in params.keys():
                config[cmd].add(tomlkit.comment(f"{param} ="))

    with config_file.open("w") as f:
        f.write(tomlkit.dumps(config))

    console.print("Exiting...")
    ctx.exit()


def load_params(ctx, param, filename):
    if not filename or ctx.resilient_parsing:
        return

    ctx.default_map = {}
    if Path(filename).is_file():
        with Path(filename).open("r") as f:
            params = tomlkit.load(f)
        if params:
            ctx.default_map = params.get(ctx.info_name, {})

    ctx.obj = {"config_file": filename}
