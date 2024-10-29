from __future__ import annotations

import shutil
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from .deps import cutadapt, fastp, starcode
from .filters import read_filter
from .options import PycashierOpts
from .scrna import labeled_fastq_to_tsv, sam_to_name_labeled_fastq
from .term import term
from .utils import (
    check_output,
    fastq_to_tsv,
    get_filter_count,
    run_cmd,
)


class SampleStatus(Enum):
    COMPLETE = 0
    INCOMPLETE = 1
    WARN = 2
    FAIL = 3


def status_check(func: Callable) -> Callable:
    def wrapper(self: Sample, *args: Any, **kwargs: Any) -> None:
        if func(self, *args, **kwargs):
            self.status = SampleStatus.FAIL

    return wrapper


class Sample:
    def __init__(self, name: str, opts: PycashierOpts) -> None:
        self.opts = opts
        self.name = name
        self.status = (
            SampleStatus.COMPLETE
            if all(self.check().values())
            else SampleStatus.INCOMPLETE
        )
        self.steps: Tuple[Callable, ...]
        self.completed = self.status is SampleStatus.COMPLETE

    def check(self) -> Dict[str, bool]:
        raise NotImplementedError

    def finished(self, success: bool = True) -> None:
        symbol = (
            "[green]✔[/]"
            if self.status == SampleStatus.COMPLETE
            else ("[yellow]⚠[/]" if self.status == SampleStatus.WARN else "[red]✘[/]")
        )
        term.print(f"[b]{symbol} {self.name}")

    def pipeline(self) -> None:
        with term.cash_in(self.name):
            for step in self.steps:
                step()
                if self.status != SampleStatus.INCOMPLETE:
                    break
        if self.status == SampleStatus.INCOMPLETE:
            self.status = SampleStatus.COMPLETE
        self.finished()


class ExtractFiles:
    def __init__(self, name: str, opts: PycashierOpts) -> None:
        self.quality = opts.pipeline / f"{name}.q{opts.quality}.fastq"
        self.barcode_fastq = self.quality.with_suffix(".barcode.fastq")
        self.barcodes = self.quality.with_suffix(".barcodes.tsv")
        # if opts.ratio doesn't look like an integer replace the decimal
        if int(opts.ratio) != opts.ratio:
            ratio_str = str(opts.ratio).replace(".", "_")
        else:
            ratio_str = str(int(opts.ratio))
        self.clustered = self.barcodes.with_suffix(f".r{ratio_str}d{opts.distance}.tsv")

    def final(self, opts: PycashierOpts) -> Optional[Path]:
        if not self.clustered.is_file():
            return None
        if opts.filter_percent:
            min_count = get_filter_count(self.clustered, float(opts.filter_percent))
        else:
            min_count = opts.filter_count
        return (opts.output / self.clustered.name).with_suffix(
            f".min{min_count}_off{opts.offset}.tsv"
        )


class ExtractSample(Sample):
    def __init__(self, fastq: Path, opts: PycashierOpts) -> None:
        name = fastq.name.split(".")[0]
        self.fastq = fastq
        self.files = ExtractFiles(name=name, opts=opts)
        self.steps = (
            self._filter,
            self._cutadapt,
            self._fast2tsv,
            self._starcode,
            self._read_filter,
        )
        super().__init__(name, opts)

    def check(self) -> Dict[str, bool]:
        exists = {}
        for name in ("quality", "barcodes", "clustered"):
            exists[name] = (file_exists := (f := getattr(self.files, name)).is_file())
            if file_exists and f.stat().st_size == 0:
                term.log.warning(f"{f} appears to be empty")

        if final := self.files.final(self.opts):
            exists["final"] = (file_exists := final.is_file())
            # size of 'barcode count'
            if file_exists and final.stat().st_size <= 14:
                term.log.warning(f"{final} appears to be empty")
        else:
            exists["final"] = False
        self.files_exist = exists
        return exists

    @status_check
    def _filter(self) -> bool | None:
        json, html = (
            self.opts.pipeline / "qc" / f"{self.name}.{ext}" for ext in ("json", "html")
        )
        msg = "quality filtering reads with fastp"
        (self.opts.pipeline / "qc").mkdir(exist_ok=True)

        if not check_output(self.files.quality, msg):
            command = (
                "fastp "
                f"-i {self.fastq} "
                f"-o {self.files.quality} "
                f"-q {self.opts.quality} "
                f"-u {self.opts.unqualified_percent} "
                f"-w {self.opts.threads} "
                f"-h {html} "
                f"-j {json} "
                f"{self.opts.fastp_args or ''} "
            )
            with term.process(msg):
                return run_cmd(
                    command, self.name, self.files.quality, self.opts.verbose
                )

    @status_check
    def _cutadapt(
        self,
    ) -> bool | None:
        """perform quality filtering and extraction"""

        msg = "extracting barcodes with cutadapt"
        adapter_string = (
            f"-g {self.opts.upstream_adapter} -a {self.opts.downstream_adapter}"
            if self.opts.unlinked_adapters
            else f"-g {self.opts.upstream_adapter}...{self.opts.downstream_adapter}"
        )

        if self.opts.skip_trimming:
            shutil.copy(self.files.quality, self.files.barcode_fastq)

        if not check_output(
            self.files.quality.with_suffix(".barcode.fastq"),
            msg,
        ):
            command = (
                cutadapt
                + " "
                + (
                    f"-e {self.opts.error} "
                    f"-j {self.opts.threads} "
                    f"--minimum-length={self.opts.length - self.opts.distance} "
                    f"--maximum-length={self.opts.length + self.opts.distance} "
                    f"{adapter_string} "
                    f"{self.opts.cutadapt_args or ''} "
                    f"-o {self.files.barcode_fastq} {self.files.quality}"
                )
            )
            with term.process(msg):
                return run_cmd(
                    command,
                    self.name,
                    self.files.barcode_fastq,
                    self.opts.verbose,
                )

    @status_check
    def _fast2tsv(self) -> bool | None:
        if not check_output(self.files.barcodes, "converting fastq to tsv"):
            return fastq_to_tsv(self.files.barcode_fastq, self.files.barcodes)

    @status_check
    def _starcode(self) -> bool | None:
        """cluster the barcodes using starcode"""

        msg = "clustering barcodes with starcode"

        if not check_output(self.files.clustered, msg):
            command = (
                starcode
                + " "
                + (
                    f"-d {self.opts.distance} -r {self.opts.ratio} "
                    f"-t {self.opts.threads} -i {self.files.barcode_fastq} -o {self.files.clustered}"
                )
            )
            with term.process(msg):
                return run_cmd(
                    command, self.name, self.files.clustered, self.opts.verbose
                )

    def _read_filter(self) -> None:
        if read_filter(self.files.clustered, self.opts):
            self.status = SampleStatus.WARN
        else:
            self.status = SampleStatus.COMPLETE


class MergeSample(Sample):
    def __init__(self, fastqR1: Path, fastqR2: Path, opts: PycashierOpts) -> None:
        name = fastqR1.name.split(".")[0]
        self.fastqR1 = fastqR1
        self.fastqR2 = fastqR2
        self.name = fastqR1.name.split(".")[0]
        self.merged = opts.output / f"{self.name}.merged.raw.fastq"
        self.steps = (self._fastp_merge,)
        super().__init__(name, opts)

    def check(self) -> Dict[str, bool]:
        exists = self.merged.is_file()
        if exists and self.merged.stat().st_size == 0:
            term.log.warning(f"{self.merged} appears to be empty")
        return {"final": exists}

    @status_check
    def _fastp_merge(
        self,
    ) -> bool | None:
        """merge a single sample with fastp"""

        msg = "merging paired end reads with fastp"
        if not check_output(self.merged, msg):
            command = (
                fastp
                + " "
                + (
                    f"-i {self.fastqR1}  "
                    f"-I {self.fastqR2}  "
                    f"-w {self.opts.threads} "
                    f"-j {self.opts.pipeline}/merge_qc/{self.name}.json "
                    f"-h {self.opts.pipeline}/merge_qc/{self.name}.html "
                    f"--merged_out {self.merged} "
                    f"{self.opts.fastp_args or ''}"
                )
            )

            with term.process(msg):
                return run_cmd(command, self.name, self.merged, self.opts.verbose)


class ScrnaSample(Sample):
    def __init__(self, sam: Path, opts: PycashierOpts) -> None:
        name = sam.name.split(".")[0]

        self.sam = sam
        self.fastq = opts.pipeline / f"{name}.umi_cell_labeled.fastq"
        self.barcode_fastq = self.fastq.with_suffix(".barcode.fastq")
        self.barcodes = opts.output / f"{name}.umi_cell_labeled.barcode.tsv"
        self.steps = (self._sam_to_fastq, self._pysam_cutadapt, self._fast_to_tsv)
        super().__init__(name, opts)

    def check(self) -> Dict[str, bool]:
        return {
            f: getattr(self, f).is_file()
            for f in ("fastq", "barcode_fastq", "barcodes")
        }

    @status_check
    def _sam_to_fastq(self) -> bool | None:
        if not check_output(self.fastq, "converting sam to labeled fastq"):
            return sam_to_name_labeled_fastq(self.name, self.sam, self.fastq)

    @status_check
    def _pysam_cutadapt(
        self,
    ) -> bool | None:
        """extract barcodes from single cell data

        Args:
           status: Rich.console status to suspend for stderr printing.
        """
        msg = "extracting barcodes with cutadapt"
        adapter_string = (
            f"-g {self.opts.upstream_adapter} -a {self.opts.downstream_adapter}"
        )

        if not check_output(self.barcode_fastq, msg):
            command = (
                cutadapt
                + " "
                + (
                    f"-e {self.opts.error} "
                    f"-j {self.opts.threads} "
                    f"--minimum-length={self.opts.minimum_length} "
                    f"--maximum-length={self.opts.length} "
                    f"{adapter_string} "
                    f"{self.opts.cutadapt_args or ''} "
                    f"-o {self.barcode_fastq} {self.fastq}"
                )
            )
            with term.process(msg):
                return run_cmd(
                    command, self.name, self.barcode_fastq, self.opts.verbose
                )

    @status_check
    def _fast_to_tsv(self) -> bool | None:
        if not check_output(self.barcodes, "converting labeled fastq to tsv"):
            return labeled_fastq_to_tsv(self.barcode_fastq, self.barcodes)
