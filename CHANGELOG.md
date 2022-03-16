# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
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

[Unreleased]: https://github.com/brocklab/pycashier/compare/v0.2.8...HEAD
