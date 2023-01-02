import filecmp
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

TEST_DIR = Path(__file__).parent
OUTS_DIR, REF_DIR, MERGED_DIR, PIPELINE_DIR = (
    TEST_DIR / "data" / name
    for name in ("outs", "reference", "mergedfastqs", "pipeline")
)


# def show_subprocess_result(p: subprocess.CompletedProcess) -> None:
#     """this is just for debugging during test development"""
#     print(f"\nstdout{'-'*50}\n{p.stdout}\n{'-'*60}")
#     print(f"\nstderr{'-'*50}\n{p.stderr}\n{'-'*60}")


def cmp_outs(filename: str, paths: Tuple[Path, Path]) -> bool:
    file_one, file_two = (filepath / filename for filepath in paths)
    return filecmp.cmp(file_one, file_two)


def pycashier_run(cmd: List[str | Path]) -> subprocess.CompletedProcess:
    p = subprocess.run(
        ["pycashier", *cmd],
        capture_output=True,
        universal_newlines=True,
    )
    return p


def test_pycashier_extract() -> None:
    if OUTS_DIR.is_dir():
        shutil.rmtree(OUTS_DIR)

    pycashier_run(
        [
            "extract",
            "-i",
            TEST_DIR / "data/reference/rawfastqgzs",
            "-o",
            TEST_DIR / "data/outs",
            "-p",
            TEST_DIR / "data/pipeline",
            "-y",
        ],
    )

    assert cmp_outs(
        "test.q30.barcodes.r3d1.min0_off1.tsv", (REF_DIR / "outs", OUTS_DIR)
    )


def test_pycashier_merge() -> None:
    if MERGED_DIR.is_dir():
        shutil.rmtree(MERGED_DIR)

    pycashier_run(
        [
            "merge",
            "-i",
            TEST_DIR / "data/reference/unmergedfastqgzs",
            "-o",
            MERGED_DIR,
            "-p",
            TEST_DIR / "data/pipeline",
            "-y",
        ],
    )

    assert cmp_outs(
        "test.q30.barcodes.r3d1.min0_off1.tsv", (REF_DIR / "outs", OUTS_DIR)
    )


def test_pycashier_scrna() -> None:
    if OUTS_DIR.is_dir():
        shutil.rmtree(MERGED_DIR)

    pycashier_run(
        [
            "scrna",
            "-i",
            TEST_DIR / "data/reference/sams",
            "-o",
            OUTS_DIR,
            "-p",
            TEST_DIR / "data/pipeline",
            "-y",
        ],
    )
    assert cmp_outs(
        "test.cell_record_labeled.barcode.tsv", (REF_DIR / "outs-scrna", OUTS_DIR)
    )
