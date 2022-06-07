# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.4] - 2022-06-07
### [Added]
- Docker image instructions
### [Changed]
- Use wider format help on bigger terminals


## [0.3.3] - 2022-05-23
### [Added]
- Dockerfile
### [Changed]
- Fix #8 to allow .fastq.gz in input directory


## [0.3.2] - 2022-04-06
### [Changed]
- Swapped `rich-click` for `click-rich-help`


## [0.3.1] - 2022-03-29
### [Added]
- `Pycashier` now manages version with `bumpver`

### [Changed]
- Dropped yaml-based config for toml


## [0.3.0] - 2022-03-16
### [Added]
- This CHANGELOG
- Combine command to simply combine output tsv's into one file
- Length offset to filter sequences post-clustering
- Option to `--skip-trimming` in extract
- Config file to improve UX

### [Changed]
- Entire CLI was redesigned around click/rich
- When performing adapter trimming the min/max length is set to length +/- Levenshtein distance
- Sample Queue table is formatted inline with new CLI
- Dropped regex in "extract" in favor of simple string matching
- Merge can take unzipped fastqs now

[Unreleased]: https://github.com/brocklab/pycashier/compare/v0.3.4...HEAD
[0.3.4]: https://github.com/brocklab/pycashier/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/brocklab/pycashier/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/brocklab/pycashier/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/brocklab/pycashier/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/brocklab/pycashier/compare/v0.2.8...v0.3.0
