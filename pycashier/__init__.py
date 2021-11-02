from ._checks import pre_run_check

__version__ = "0.2.0"

PACKAGES = ["starcode", "cutadapt", "fastq_quality_filter"]

pre_run_check(PACKAGES)
