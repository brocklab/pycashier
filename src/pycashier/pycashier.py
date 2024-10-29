from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any, Generator, List

import click

from .config import save_params
from .merge import get_pefastqs
from .options import PycashierOpts
from .receipt import receipt
from .sample import ExtractSample, MergeSample, Sample, ScrnaSample
from .term import term
from .termui import confirm_extract_samples, confirm_samples, print_params
from .utils import filter_input_by_sample


class Pycashier:
    def __init__(self, ctx: click.Context, save_config: bool, **kwargs: Any) -> None:
        self.opts = PycashierOpts(**kwargs)
        if not (parent := self.opts.pipeline.parent).is_dir():
            term.print(
                f"[InputError] pipeline parent directory, {parent}, does not exist.",
                err=True,
            )
            term.quit()
        self.opts.pipeline.mkdir(exist_ok=True)
        term.set_logger(self.opts.log_file, self.opts.verbose)

        # must be after logger is initialized
        term.log.debug("pycashier command line:\n  " + " ".join(sys.argv))
        self.mode = str(ctx.info_name)
        self.check_duplicates = self.mode != "merge"
        term.mode(cmd=self.mode)
        if save_config:
            save_params(ctx)
        print_params(ctx)

    def _get_input_files(
        self,
        exts: List[str],
    ) -> List[Path]:
        """determine input files
        Args:
            samples: List of allowed samples.
            exts: Acceptable file extensions.

        Returns:
            List of fastq/sam files (may be gzipped).
        """

        candidate_files = [
            f for f in self.opts.input_.iterdir() if not f.name.startswith(".")
        ]

        if not candidate_files:
            term.print(
                f"[InputError]: Source dir: {self.opts.input_}, appears to be empty...",
                err=True,
            )
            term.quit()

        bad_files = [
            f.name
            for f in candidate_files
            if not any(f.name.endswith(suffix) for suffix in exts)
        ]
        symlinks = [f for f in candidate_files if f.is_symlink() and not f.exists()]
        duplicates = []

        if self.check_duplicates:
            duplicates = [
                name
                for name, count in Counter(
                    [f.name.split(".")[0] for f in candidate_files]
                ).items()
                if count > 1
            ]

        if bad_files:
            term.print(
                f"[InputError]: There is a non [bold]{'/'.join(exts)}[/] file in the provided input directory: "
                + "; ".join((f"[red]{file}[/]") for file in bad_files),
                err=True,
            )
        if symlinks:
            term.print(
                f"[InputError]: There is a symlink in the provided input directory: {';'.join((link.name for link in symlinks))} \n"
                "If using docker: Ensure that symlinks are resolved within the mounted volume "
                "in '/data' or pycashier within docker won't find them.",
                err=True,
            )

        if duplicates:
            # NOTE: if running with receipt then the message should be different
            term.print(
                "[InputError]: There appears to be duplicates files in input directory for sample(s): "
                f"{';'.join((dup for dup in duplicates))} \n"
                "See [b]pycashier merge[/b] for overlapping PE reads.",
                err=True,
            )

        if bad_files or symlinks or duplicates:
            term.quit()

        if self.opts.samples:
            candidate_files = filter_input_by_sample(
                candidate_files, self.opts.samples.split(",")
            )

        return candidate_files

    def _log_samples(
        self, samples: List[ExtractSample] | List[MergeSample] | List[ScrnaSample]
    ) -> None:
        term.log.debug(
            f"processing {len(samples)} samples: "
            + ";".join((sample.name for sample in samples))
        )

    def _process_samples(
        self, samples: List[ExtractSample] | List[MergeSample] | List[ScrnaSample]
    ) -> Generator[Sample, None, None]:
        for sample in samples:
            term.log.debug(f"starting sample: {sample.name}")
            yield sample

    def _is_complete(
        self, samples: List[ExtractSample] | List[MergeSample] | List[ScrnaSample]
    ) -> None:
        if all((sample.completed for sample in samples)):
            term.quit(0)

    def _check_failure(
        self, samples: List[ExtractSample] | List[MergeSample] | List[ScrnaSample]
    ) -> None:
        failed = [sample for sample in samples if sample.status.value == 3]

        if failed:
            term.print(
                f"\n\nFailed to complete {len(failed)} samples.\n"
                f"See [hl]{self.opts.log_file}[/] for more info.",
                err=True,
            )

    def extract(
        self,
        ctx: click.Context,
        yes: bool,  # TODO: this should be accessed...
        **kwargs: Any,
    ) -> None:
        """
        extract DNA barcodes from a directory of fastq files

        \b
        Sample names should be delimited with a ".", such as `[hl][yellow]<sample>[/yellow].raw.fastq[/]`,
        anything succeeding the first period will be ignored by `[hl]pycashier[/]`.

        If your data is paired-end with overlapping barcodes,
        see `[hl]pycashier merge[/]`.
        """

        # validate that filter count and filter percent aren't both defined
        self.opts.update_filter(ctx)

        with term.cash_in(f"checking {self.opts.pipeline}"):
            samples = [
                ExtractSample(fastq=f, opts=self.opts)
                for f in self._get_input_files(
                    exts=[".fastq", ".fastq.gz"],
                )
            ]

        confirm_extract_samples(samples, self.opts)
        self._is_complete(samples)

        self.opts.output.mkdir(exist_ok=True)

        samples = [sample for sample in samples if not sample.completed]
        self._log_samples(samples)
        for sample in self._process_samples(samples):
            sample.pipeline()
        self._check_failure(samples)

    def merge(
        self,
    ) -> None:
        """
        merge overlapping paired-end reads using fastp
        \n\n\n
        Simple wrapper over `[hl]fastp[/]` to combine R1 and R2 from PE fastq files.
        \n\n\n
        """

        samples = [
            MergeSample(fastqR1=fastqs["R1"], fastqR2=fastqs["R2"], opts=self.opts)
            for s, fastqs in get_pefastqs(
                self._get_input_files(
                    exts=[".fastq", ".fastq.gz"],
                )
            ).items()
        ]

        confirm_samples(samples, self.opts)

        self._is_complete(samples)
        self.opts.output.mkdir(exist_ok=True)

        samples = [sample for sample in samples if not sample.completed]
        for sample in samples:
            sample.pipeline()

        self._check_failure(samples)

    def scrna(
        self,
    ) -> None:
        """
        extract expressed DNA barcodes from scRNA-seq
        \n
        \b
        Designed for interoperability with 10X scRNA-seq workflow.
        After processing samples with `[hl]cellranger[/]` resulting
        bam files should be converted to sam files using `[hl]samtools[/]`.
        \n
        [i]NOTE[/]: You can speed this up by providing a sam file with only
        the unmapped reads.
        """
        samples = [
            ScrnaSample(sam=f, opts=self.opts)
            for f in self._get_input_files(exts=[".sam"])
        ]
        confirm_samples(samples, self.opts)
        self._is_complete(samples)
        self.opts.output.mkdir(exist_ok=True)

        samples = [sample for sample in samples if not sample.completed]
        for sample in samples:
            sample.pipeline()
        self._check_failure(samples)

    def receipt(
        self,
    ) -> None:
        """
        combine and summarize outputs of [hl]extract[/]
        """

        files = {f.name.split(".")[0]: f for f in self._get_input_files(exts=[".tsv"])}
        with term.cash_in("calculating"):
            receipt(files, self.opts)
