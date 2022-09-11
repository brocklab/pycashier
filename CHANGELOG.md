# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to a type of [CalVer](https://calver.org).

version -> vYY.MM.PATCH

## Unreleased
### Changed
- made init check dependent on command run (fixes #10)
- ignore hidden files in input directory (fixes #9)
- simplified detection of PE reads
- several UI changes for clarity and simplicity

### Added
- check for config file and exit if it doesn't exist
- separate `rich.console.Console` for stderr outputs

## [22.6.2] - 2022-06-30
### Added
- new `-y/--yes` flag to skip prompts

### Changed
- switch project management to pdm
- improved merge error message
- made docker build multi-stage to reduce footprint
- updated ci to use python action instead of poetry

## [22.6.1] - 2022-06-27
### Fixed
- Fixed(#8)

### Changed
- refactored cli source for simplicity
- project now adheres to [CalVer](https://calver.org)

## [0.3.5] - 2022-06-17
### Added
- Encourage user to increase thread count

### Changed
- Drop `just` for `make` to streamline development

## [0.3.4] - 2022-06-07
### Added
- Docker image instructions

### Changed
- Use wider format help on bigger terminals


## [0.3.3] - 2022-05-23
### Added
- Dockerfile

### Changed
- Fix #8 to allow .fastq.gz in input directory


## [0.3.2] - 2022-04-06
### Changed
- Swapped `rich-click` for `click-rich-help`


## [0.3.1] - 2022-03-29
### Added
- `Pycashier` now manages version with `bumpver`

### Changed
- Dropped yaml-based config for toml


## [0.3.0] - 2022-03-16
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

[Unreleased]: https://github.com/brocklab/pycashier/compare/v22.6.2...HEAD
[22.6.2]: https://github.com/brocklab/pycashier/compare/v22.6.1...v22.6.2
[22.6.1]: https://github.com/brocklab/pycashier/compare/v0.3.5...v22.6.1
[0.3.5]: https://github.com/brocklab/pycashier/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/brocklab/pycashier/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/brocklab/pycashier/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/brocklab/pycashier/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/brocklab/pycashier/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/brocklab/pycashier/compare/v0.2.8...v0.3.0
