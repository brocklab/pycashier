import subprocess
import tempfile
from pathlib import Path

import pysam
from rich.progress import Progress

from .console import console


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
