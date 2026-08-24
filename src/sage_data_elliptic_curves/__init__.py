"""Access the elliptic-curve databases without depending on SageMath."""

from __future__ import annotations

import ast
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any


__version__ = "0.8.1"
__all__ = [
    "EllipticCurveRecord",
    "available_ranks",
    "cremona_mini_connection",
    "cremona_mini_path",
    "cremona_mini_resource",
    "data_root",
    "iter_rank",
    "rank_path",
    "rank_resource",
]


@dataclass(frozen=True, slots=True)
class EllipticCurveRecord:
    """One record from a rank-grouped elliptic-curve text database."""

    conductor: int
    isogeny_class: str
    number: int
    ainvs: tuple[int, int, int, int, int]
    rank: int
    torsion_order: int

    @property
    def class_label(self) -> str:
        """Return the Cremona isogeny-class label, such as ``11a``."""
        return f"{self.conductor}{self.isogeny_class}"

    @property
    def label(self) -> str:
        """Return the full Cremona curve label, such as ``11a1``."""
        return f"{self.class_label}{self.number}"


def data_root() -> Any:
    """Return the package's data root as an importlib resource traversable."""
    return files("sage_data_elliptic_curves.data")


def cremona_mini_resource() -> Any:
    """Return the mini Cremona SQLite database resource."""
    return data_root().joinpath("cremona", "cremona_mini.db")


def _validate_rank(rank: int) -> int:
    if isinstance(rank, bool) or not isinstance(rank, int):
        raise TypeError("rank must be an integer")
    if rank < 0:
        raise ValueError("rank must be nonnegative")
    return rank


def available_ranks() -> tuple[int, ...]:
    """Return the ranks for which a packaged text database is available."""
    ranks = []
    for resource in data_root().joinpath("ellcurves").iterdir():
        suffix = resource.name.removeprefix("rank")
        if resource.name.startswith("rank") and suffix.isdigit():
            ranks.append(int(suffix))
    return tuple(sorted(ranks))


def rank_resource(rank: int) -> Any:
    """Return the text-database resource for ``rank``.

    Raise :class:`FileNotFoundError` if this distribution has no data for the
    requested rank.
    """
    rank = _validate_rank(rank)
    if rank not in available_ranks():
        raise FileNotFoundError(f"no elliptic-curve database for rank {rank}")
    return data_root().joinpath("ellcurves", f"rank{rank}")


@contextmanager
def cremona_mini_path() -> Iterator[Path]:
    """Yield a filesystem path to the mini Cremona database resource."""
    with as_file(cremona_mini_resource()) as path:
        yield path


@contextmanager
def rank_path(rank: int) -> Iterator[Path]:
    """Yield a filesystem path to the text database for ``rank``."""
    with as_file(rank_resource(rank)) as path:
        yield path


@contextmanager
def cremona_mini_connection() -> Iterator[sqlite3.Connection]:
    """Yield a read-only SQLite connection to the mini Cremona database."""
    with cremona_mini_path() as path:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        try:
            connection.execute("PRAGMA query_only = ON")
            yield connection
        finally:
            connection.close()


def _parse_record(line: str, source: str, line_number: int) -> EllipticCurveRecord:
    try:
        conductor, isogeny_class, number, encoded_ainvs, rank, torsion = line.split()
        parsed_ainvs = ast.literal_eval(encoded_ainvs)
        if (
            not isinstance(parsed_ainvs, list)
            or len(parsed_ainvs) != 5
            or any(isinstance(value, bool) or not isinstance(value, int) for value in parsed_ainvs)
        ):
            raise ValueError("a-invariants must be a list of five integers")
        ainvs = tuple(parsed_ainvs)
        return EllipticCurveRecord(
            conductor=int(conductor),
            isogeny_class=isogeny_class,
            number=int(number),
            ainvs=ainvs,
            rank=int(rank),
            torsion_order=int(torsion),
        )
    except (SyntaxError, TypeError, ValueError) as error:
        raise ValueError(f"malformed record at {source}:{line_number}") from error


def iter_rank(rank: int) -> Iterator[EllipticCurveRecord]:
    """Iterate over the elliptic-curve records stored for ``rank``."""
    rank = _validate_rank(rank)
    resource = rank_resource(rank)
    with resource.open("r", encoding="ascii") as source:
        for line_number, line in enumerate(source, 1):
            record = _parse_record(line, resource.name, line_number)
            if record.rank != rank:
                raise ValueError(
                    f"record at {resource.name}:{line_number} has rank "
                    f"{record.rank}, expected {rank}"
                )
            yield record
