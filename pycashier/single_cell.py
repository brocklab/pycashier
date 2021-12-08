import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import pysam
except ImportError:
    pass

from rich.progress import Progress

from .console import console


def sam_to_name_labeled_fastq(sample, in_file, out_file):

    new_sam = False

    with open(in_file, "r") as f_in:
        if f_in.readline()[0:3] != "@HD":
            new_sam = True

    if new_sam:
        console.log(f"[green]{sample}[/green]: sam is headerless, adding a fake one")
        sam_file = fake_header_add(in_file)
    else:
        sam_file = in_file

    sam_length = pysam.AlignmentFile(sam_file, "r", check_sq=False).count()
    sam = pysam.AlignmentFile(sam_file, "r", check_sq=False)

    with open(out_file, "w") as f_out:

        with Progress() as progress:
            task = progress.add_task("[red] Converting sam to fastq", total=sam_length)

            for record in sam:

                tagdict = dict(record.tags)
                cell_barcode = None
                if "CB" in tagdict.keys():
                    cell_barcode = tagdict["CB"].split("-")[0]
                elif "CR" in tagdict.keys():
                    cell_barcode = tagdict["CR"]

                umi = None
                if "UB" in tagdict.keys():
                    umi = tagdict["UB"]
                elif "UR" in tagdict.keys():
                    umi = tagdict["UR"]

                if cell_barcode and umi:

                    qualities = record.query_qualities
                    ascii_qualities = "".join([chr(q + 33) for q in qualities])

                    f_out.write(f"@{record.query_name}_{umi}_{cell_barcode}\n")
                    f_out.write(f"{record.query_sequence}\n+\n{ascii_qualities}\n")

                progress.advance(task)

    if new_sam:

        Path(sam_file).unlink()


def labeled_fastq_to_tsv(in_file, out_file):

    with open(in_file) as f_in:

        with open(out_file, "w") as f_out:
            read_lines = []
            # TODO: add progress bar
            for line in f_in.readlines():
                read_lines.append(line)
                if len(read_lines) == 4:

                    read_name, umi, cell_barcode = read_lines[0].rstrip("\n").split("_")
                    lineage_barcode = read_lines[1].rstrip("\n")

                    f_out.write(
                        f"{read_name}\t{umi}\
                            \t{cell_barcode}\t{lineage_barcode}\n"
                    )
                    read_lines = []


def fake_header_add(in_file):

    fake_header = """@HD\tVN:1.6\tSO:coordinate
@SQ\tSN:1\tLN:1000
@SQ\tSN:2\tLN:1000
@SQ\tSN:3\tLN:1000
@SQ\tSN:4\tLN:1000
@SQ\tSN:5\tLN:1000
@SQ\tSN:6\tLN:1000
@SQ\tSN:7\tLN:1000
@SQ\tSN:8\tLN:1000
@SQ\tSN:9\tLN:1000
@SQ\tSN:10\tLN:1000
@SQ\tSN:11\tLN:1000
@SQ\tSN:12\tLN:1000
@SQ\tSN:13\tLN:1000
@SQ\tSN:14\tLN:1000
@SQ\tSN:15\tLN:1000
@SQ\tSN:16\tLN:1000
@SQ\tSN:17\tLN:1000
@SQ\tSN:18\tLN:1000
@SQ\tSN:19\tLN:1000
@SQ\tSN:20\tLN:1000
@SQ\tSN:21\tLN:1000
@SQ\tSN:22\tLN:1000
@SQ\tSN:23\tLN:1000
@SQ\tSN:X\tLN:1000
@SQ\tSN:Y\tLN:1000
@SQ\tSN:MT\tLN:1000
@SQ\tSN:GL000192.1\tLN:1000
@SQ\tSN:GL000225.1\tLN:1000
@SQ\tSN:GL000194.1\tLN:1000
@SQ\tSN:GL000193.1\tLN:1000
@SQ\tSN:GL000200.1\tLN:1000
@SQ\tSN:GL000222.1\tLN:1000
@SQ\tSN:GL000212.1\tLN:1000
@SQ\tSN:GL000195.1\tLN:1000
@SQ\tSN:GL000223.1\tLN:1000
@SQ\tSN:GL000224.1\tLN:1000
@SQ\tSN:GL000219.1\tLN:1000
@SQ\tSN:GL000205.1\tLN:1000
@SQ\tSN:GL000215.1\tLN:1000
@SQ\tSN:GL000216.1\tLN:1000
@SQ\tSN:GL000217.1\tLN:1000
@SQ\tSN:GL000199.1\tLN:1000
@SQ\tSN:GL000211.1\tLN:1000
@SQ\tSN:GL000213.1\tLN:1000
@SQ\tSN:GL000220.1\tLN:1000
@SQ\tSN:GL000218.1\tLN:1000
@SQ\tSN:GL000209.1\tLN:1000
@SQ\tSN:GL000221.1\tLN:1000
@SQ\tSN:GL000214.1\tLN:1000
@SQ\tSN:GL000228.1\tLN:1000
@SQ\tSN:GL000227.1\tLN:1000
@SQ\tSN:GL000191.1\tLN:1000
@SQ\tSN:GL000208.1\tLN:1000
@SQ\tSN:GL000198.1\tLN:1000
@SQ\tSN:GL000204.1\tLN:1000
@SQ\tSN:GL000233.1\tLN:1000
@SQ\tSN:GL000237.1\tLN:1000
@SQ\tSN:GL000230.1\tLN:1000
@SQ\tSN:GL000242.1\tLN:1000
@SQ\tSN:GL000243.1\tLN:1000
@SQ\tSN:GL000241.1\tLN:1000
@SQ\tSN:GL000236.1\tLN:1000
@SQ\tSN:GL000240.1\tLN:1000
@SQ\tSN:GL000206.1\tLN:1000
@SQ\tSN:GL000232.1\tLN:1000
@SQ\tSN:GL000234.1\tLN:1000
@SQ\tSN:GL000202.1\tLN:1000
@SQ\tSN:GL000238.1\tLN:1000
@SQ\tSN:GL000244.1\tLN:1000
@SQ\tSN:GL000248.1\tLN:1000
@SQ\tSN:GL000196.1\tLN:1000
@SQ\tSN:GL000249.1\tLN:1000
@SQ\tSN:GL000246.1\tLN:1000
@SQ\tSN:GL000203.1\tLN:1000
@SQ\tSN:GL000197.1\tLN:1000
@SQ\tSN:GL000245.1\tLN:1000
@SQ\tSN:GL000247.1\tLN:1000
@SQ\tSN:GL000201.1\tLN:1000
@SQ\tSN:GL000235.1\tLN:1000
@SQ\tSN:GL000239.1\tLN:1000
@SQ\tSN:GL000210.1\tLN:1000
@SQ\tSN:GL000231.1\tLN:1000
@SQ\tSN:GL000229.1\tLN:1000
@SQ\tSN:GL000226.1\tLN:1000
"""
    # TODO: change to with statement
    f = tempfile.NamedTemporaryFile(delete=False, dir=Path.cwd())
    # print(f'copying new tmp sam to {f.name}')
    f.write((bytes(fake_header, encoding="utf-8")))
    f.flush()

    subprocess.run(["cat", in_file], stdout=f)

    # #python implementation
    # with open(in_file, 'r') as sam_file:
    #     for line in sam_file:
    #         f.write(bytes(line, encoding='utf-8'))
    #    #f.write(bytes(sam_file.read()), encoding='utf-8')

    f.close()
    return f.name


def single_cell_process(sample, f, sourcedir, cli_args, status):

    error_rate = cli_args["extract"]["error_rate"]
    threads = cli_args["main"]["threads"]
    barcode_length_min = 10
    barcode_length = cli_args["extract"]["barcode_length"]
    upstream_adapter = cli_args["extract"]["upstream_adapter"]
    downstream_adapter = cli_args["extract"]["downstream_adapter"]
    adapter_string = f"-g {upstream_adapter} -a {downstream_adapter}"

    input_file = f
    pipeline_dir = Path(cli_args["main"]["pipelinedir"])
    fastq_out = pipeline_dir / f"{sample}.cell_record_labeled.fastq"
    output_file = pipeline_dir / f"{sample}.cell_record_labeled.barcode.fastq"
    tsv_out = (
        Path(cli_args["main"]["outdir"]) / f"{sample}.cell_record_labeled.barcode.tsv"
    )

    if not fastq_out.is_file():
        console.log(f"[green]{sample}[/green]: converting sam to labeled fastq")
        status.stop()
        sam_to_name_labeled_fastq(sample, input_file, fastq_out)
        status.start()
    else:
        console.log(
            f"[green]{sample}[/green]: skipping sam to labeled fastq conversion"
        )

    if not output_file.is_file():

        console.log(f"[green]{sample}[/green]: extracting barcodes")

        command = f"cutadapt \
            -e {error_rate} \
            -j {threads} \
            --minimum-length={barcode_length_min} \
            --maximum-length={barcode_length} \
            --max-n=0 \
            --trimmed-only {adapter_string} \
            -n 2 \
            -o {output_file} {fastq_out}"

        args = shlex.split(command)

        p = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        if cli_args["main"]["verbose"]:
            console.print("[yellow]CUTADAPT OUTPUT:")
            console.print(p.stdout)

    if not tsv_out.is_file():
        console.log(f"[green]{sample}[/green]: converting labeled fastq to tsv")
        labeled_fastq_to_tsv(output_file, tsv_out)

    else:
        console.log(
            f"[green]{sample}[/green]: skipping labeled fastq to tsv conversion"
        )


def single_cell(sourcedir, cli_args):

    console.rule("SINGLE CELL MODE", align="center", style="red")
    print()

    sam_files = [f for f in sourcedir.iterdir()]

    for f in sam_files:

        ext = f.suffix

        if ext != ".sam":
            raise ValueError("There is a non sam file in the provided input directory:")

    for f in sam_files:

        sample = f.name.split(".")[0]

        with console.status(
            f"Processing sample: [green]{sample}[/green]", spinner="dots12"
        ) as status:
            single_cell_process(sample, f, sourcedir, cli_args, status)

        console.log(f"[green]{sample}[/green]: processing completed")
        console.rule()

    console.print("\n[green]FINISHED!")
    sys.exit()
