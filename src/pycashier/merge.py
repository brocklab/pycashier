import re
from pathlib import Path
from typing import Dict, List

from .term import term


def get_pefastqs(fastqs: List[Path]) -> Dict[str, Dict[str, Path]]:
    """parse input files for paired-end sequences

    Args:
        fastqs: list of fastq files from input directory
    Returns:
        dictionary of sample and paired-end fastq files
    """
    pefastqs: Dict[str, Dict[str, Path]] = {}
    for f in fastqs:
        m = re.search(r"(?P<sample>.+?)\..*(?P<read>R[1-2])\..*fastq(?:.gz)?", f.name)
        if m:
            sample, read = m.groups()
            pefastqs.setdefault(sample, {})

            if read not in pefastqs[sample]:
                pefastqs[sample][read] = f
            else:
                term.print(
                    f"[MergeError]: detected multiple [hl]{read}[/] files for [hl]{sample}[/]\n"
                    f"files: [b]{f}[/] and [b]{pefastqs[sample][read]}[/]",
                    err=True,
                )
                term.quit()
        else:
            term.print(
                f"[MergeError]: failed to obtain sample/read info from [b]{f}[/]\n",
                "Merge mode expects fastq(.gz) files with R1 or R2 in the name",
                err=True,
            )
            term.quit()

    for sample, reads in pefastqs.items():
        if len(reads) != 2:
            term.print(
                "[MergeError]: please ensure there is and R1 and R2 for all samples"
            )
            term.print("[MergeError]: detected the following samples")
            term.print(pefastqs)
            term.quit()

    return pefastqs
