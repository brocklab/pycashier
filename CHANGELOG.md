# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to a type of [CalVer](https://calver.org).

version -> vYYYY.BUILD
where BUILD is a lexicographically increasing number:
i.e. 1001, 1002, ..., 1999, 22000

## Unreleased

## 2024.1007 - 2024-10-29

### Fixed

- changed ratio to a float (#42)

### Changed

- use pixi v0.34 for dev env/docker build
- bumped minimum polars to 1.10.0

## 2024.1006 - 2024-09-30

### Changed

- minimum python version bumped to 3.9

### Added

- override runtime executables with env vars (#31)

### Fixed

- proper exit code when nothing to process (#37)
- remove erroneous debug print (#28)

## 2024.1005 - 2024-09-19

### Changed

-  change python reqs to >=3.8
-  upgraded pixi to v0.28.2

## 2024.1004 - 2024-04-02

### Changed

- upgraded pixi to v0.18 for pyproject.toml support

### Fixed

- fix(#25)
- actually fix(#17)

## 2024.1003 - 2024-03-21

### Changed

- Docker container uses pixi for tighter control (actual lock file)

### Fixed

- warn user if there is a permission error on local directory
- #22

## 2024.1002 - 2024-02-22

### Fixed

- #21

## 2024.1001 - 2024-02-21

This release followed a major refactor and some things may be missing from the changelog.
Please see the documentation for up to date usage instructions.

### Added

- sphinx-based documentation website
- a log file produced in `./pipeline` which includes all subproccess output
- added polars to dependencies to improve tabulated data operations
- made at least one test case for all commands
- hidden `checks` command to invoke pre-run checks on demand for debugging

### Changed

- new version scheme of YYYY.BUILD
- pycashier will proceed even if a sample fails
- output is less verbose
- combine is now receipt and includes headers and basic calculations
- headers are included in all final tsvs

### Fixed

- visual indicator of work when running counts on files (#18)
- filename regex for merge is less stringent (#17)
- won't fail if unneeded program is missing (#16)

## 23.1.2 - 2023-01-07

### Changed

- updated ci pipeline to incorporate test prior to a tagged release

### Fixed

- remove `|` type operator for python <3.10 compatibility (#13)
- ensure init-check is run (#14)

## 23.1.1 - 2023-01-05

### Added

- sample parameter for all subcommands
- added some broad input/output tests
- global parameters (i.e. threads or samples to fallback on)

### Changed

- update python version requirements to >=3.8,<3.11
- updated conda lock file for docker and pinned based images to sha256 for reproducibility

### Fixed

- stop merge if both R1 and R2 not found
- removed extra whitespace in single cell output tsv
- added warning about broken symlinks (especially for docker) (#12)

## 22.10.1 - 2022-10-21

### Added

- typechecking w/Mypy

### Changed

- pinned docker image base to stable tag

## 22.9.1 - 2022-09-11

### Changed

- made init check dependent on command run (fixes #10)
- ignore hidden files in input directory (fixes #9)
- simplified detection of PE reads
- several UI changes for clarity and simplicity

### Added

- check for config file and exit if it doesn't exist
- separate `rich.console.Console` for stderr outputs
- automated docker build and switched to ghcr.io

## 22.6.2 - 2022-06-30

### Added

- new `-y/--yes` flag to skip prompts

### Changed

- switch project management to pdm
- improved merge error message
- made docker build multi-stage to reduce footprint
- updated ci to use python action instead of poetry

## 22.6.1 - 2022-06-27

### Fixed

- Fixed(#8)

### Changed

- refactored cli source for simplicity
- project now adheres to [CalVer](https://calver.org)

## 0.3.5 - 2022-06-17

### Added

- Encourage user to increase thread count

### Changed

- Drop `just` for `make` to streamline development

## 0.3.4 - 2022-06-07

### Added

- Docker image instructions

### Changed

- Use wider format help on bigger terminals

## 0.3.3 - 2022-05-23

### Added

- Dockerfile

### Changed

- Fix #8 to allow .fastq.gz in input directory

## 0.3.2 - 2022-04-06

### Changed

- Swapped `rich-click` for `click-rich-help`

## 0.3.1 - 2022-03-29

### Added

- `Pycashier` now manages version with `bumpver`

### Changed

- Dropped yaml-based config for toml


## 0.3.0 - 2022-03-16

### Added

- This CHANGELOG
- Combine command to simply combine output tsv's into one file
- Length offset to filter sequences post-clustering
- Option to `--skip-trimming` in extract
- Config file to improve UX

### Changed

- Entire CLI was redesigned around click/rich
- When performing adapter trimming the min/max length is set to length +/- Levenshtein distance
- Sample Queue table is formatted inline with new CLI
- Dropped regex in "extract" in favor of simple string matching
- Merge can take unzipped fastqs now
