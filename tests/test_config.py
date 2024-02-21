import typing
from pathlib import Path

import pytest
import tomlkit
from pycashier.cli import extract
from utils import click_run, purge

TEST_DIR = Path(__file__).parent
OUTS_DIR, REF_DIR, MERGED_DIR, PIPELINE_DIR = (
    TEST_DIR / "data" / name
    for name in ("outs", "reference", "mergedfastqs", "pipeline")
)


@pytest.mark.parametrize("config_type", ["full", "explicit"])
def test_pycashier_extract_config(config_type: str) -> None:
    config_path = Path(TEST_DIR / "data" / "pycashier.toml")
    purge(OUTS_DIR, PIPELINE_DIR, config_path)
    config_path.touch(exist_ok=True)
    # shutil.copyfile(Path(TEST_DIR / "data" / "reference" / "test.toml"), config)

    result = click_run(
        extract,
        # must provide input...
        [
            "-i",
            str(REF_DIR / "rawfastqgzs"),
            "-e",
            0.15,
            "-fc",
            5,
            "-c",
            config_path,
            "--save-config",
            config_type,
        ],
        input="n\n",
    )
    assert result.exit_code == 0
    check_config("extract")


def read_config(p: Path) -> tomlkit.TOMLDocument:
    return tomlkit.loads(p.read_text())


# tomlkit has weird types
@typing.no_type_check
def check_config(section: str) -> None:
    ref = read_config(REF_DIR / "pycashier.toml")
    config = read_config(TEST_DIR / "data" / "pycashier.toml")
    for k, v in ref[section].items():
        if k in config[section]:
            assert config[section][k] == v
