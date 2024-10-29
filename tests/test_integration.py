from pathlib import Path
from typing import List

import pytest
from click import BaseCommand
from pycashier.cli import checks, cli, extract, merge, receipt, scrna
from utils import click_run, cmp_outs, purge

TEST_DIR = Path(__file__).parent
OUTS_DIR, REF_DIR, MERGED_DIR, PIPELINE_DIR = (
    TEST_DIR / "data" / name
    for name in ("outs", "reference", "mergedfastqs", "pipeline")
)


def test_help() -> None:
    for cmd in cli, extract, merge, scrna, receipt:
        result = click_run(cmd, ["--help"])
        assert result.exit_code == 0


def test_pycashier_checks() -> None:
    result = click_run(
        checks,
    )
    assert result.exit_code == 0


@pytest.mark.parametrize(
    ("cmd", "input_dir", "pipe_dir", "ref_dir", "outs_dir", "file_name", "options"),
    (
        (
            extract,
            REF_DIR / "rawfastqgzs",
            PIPELINE_DIR / "pipe-extract",
            REF_DIR / "outs",
            OUTS_DIR,
            "test.q30.barcodes.r3d1.min0_off1.tsv",
            [],
        ),
        (
            extract,
            REF_DIR / "rawfastqgzs",
            PIPELINE_DIR / "pipe-extract-fc0",
            REF_DIR / "outs",
            OUTS_DIR,
            "test.q30.barcodes.r3d1.min0_off1.tsv",
            ["--filter-count", "0"],
        ),
        # brocklab/pycashier#42
        (
            extract,
            REF_DIR / "rawfastqgzs",
            PIPELINE_DIR / "pipe-extract-float-ratio",
            REF_DIR / "outs-float-ratio",
            OUTS_DIR,
            "test.q30.barcodes.r3_1d1.min0_off1.tsv",
            ["--ratio", "3.1"],
        ),
        (
            scrna,
            REF_DIR / "sams",
            PIPELINE_DIR / "pipe-scrna",
            REF_DIR / "outs-scrna",
            OUTS_DIR,
            "test.umi_cell_labeled.barcode.tsv",
            [],
        ),
        (
            merge,
            REF_DIR / "unmergedfastqgzs",
            PIPELINE_DIR / "pipe-merge",
            REF_DIR / "mergedfastqs",
            MERGED_DIR,
            "test.merged.raw.fastq",
            [],
        ),
    ),
)
def test_pycashier(
    cmd: BaseCommand,
    input_dir: Path,
    pipe_dir: Path,
    ref_dir: Path,
    outs_dir: Path,
    file_name: str,
    options: List[str],
) -> None:
    PIPELINE_DIR.mkdir(exist_ok=True, parents=True)
    purge(outs_dir, pipe_dir)

    result = click_run(
        cmd,
        ["-i", input_dir, "-o", outs_dir, "-p", pipe_dir, "-y", *options],
    )

    print(result.output)
    assert result.exit_code == 0
    assert cmp_outs(file_name, (ref_dir, outs_dir))


def test_pycashier_receipt() -> None:
    PIPELINE_DIR.mkdir(exist_ok=True, parents=True)
    outfile = TEST_DIR / "data/combined.tsv"
    purge(outfile, PIPELINE_DIR / "pipe-receipt")

    result = click_run(
        receipt,
        ["-i", REF_DIR / "outs", "-p", PIPELINE_DIR / "pipe-receipt", "-o", outfile],
    )

    print(result.output)
    assert result.exit_code == 0
    assert cmp_outs("combined.tsv", (REF_DIR, TEST_DIR / "data"))
