"""Generate the databases shipped by ``sage-data-elliptic-curves``.

This is adapted from the generator introduced in SageMath pull request #42701.
It intentionally uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import sqlite3
import tempfile
from contextlib import ExitStack
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SOURCES_ROOT = PROJECT_ROOT / "sources"
DATA_ROOT = PROJECT_ROOT / "src" / "sage_data_elliptic_curves" / "data"
ALLCURVES = SOURCES_ROOT / "common" / "allcurves.00000-09999"
RANK_SOURCES = SOURCES_ROOT / "ellcurves"


def create_cremona_database(allcurves: Path, output: Path) -> None:
    """Create the mini Cremona SQLite database from ``allcurves``."""
    output.unlink(missing_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    class_data = []
    curve_data = []
    with allcurves.open(encoding="ascii") as source:
        for line_number, line in enumerate(source, 1):
            try:
                conductor, isogeny_class, number, equation, rank, torsion = (
                    line.split()
                )
            except ValueError as error:
                raise ValueError(
                    f"{allcurves}:{line_number}: expected six fields"
                ) from error
            label = conductor + isogeny_class
            curve = label + number
            if number == "1":
                class_data.append((conductor, label, rank))
            curve_data.append((curve, label, equation, torsion))

    with sqlite3.connect(output) as connection:
        connection.executescript(
            """
            CREATE TABLE t_class(
                rank INTEGER,
                class TEXT PRIMARY KEY,
                conductor INTEGER
            );
            CREATE TABLE t_curve(
                curve TEXT PRIMARY KEY,
                class TEXT,
                tors INTEGER,
                eqn TEXT UNIQUE
            );
            CREATE INDEX i_t_class_conductor ON t_class(conductor);
            CREATE INDEX i_t_curve_class ON t_curve(class);
            """
        )
        connection.executemany(
            "INSERT INTO t_class(conductor, class, rank) VALUES (?, ?, ?)",
            class_data,
        )
        connection.executemany(
            "INSERT INTO t_curve(curve, class, eqn, tors) VALUES (?, ?, ?, ?)",
            curve_data,
        )


def _rank_number(path: Path) -> int:
    """Return the numeric suffix of a ``rankN`` path."""
    name = path.name
    if not name.startswith("rank") or not name[4:].isdigit():
        raise ValueError(f"invalid rank filename: {path}")
    return int(name[4:])


def rank_names(allcurves: Path, rank_sources: Path) -> tuple[str, ...]:
    """Return all rank resource names required by the input datasets."""
    ranks = set()
    with allcurves.open(encoding="ascii") as source:
        for line_number, line in enumerate(source, 1):
            fields = line.split()
            if len(fields) != 6:
                raise ValueError(f"{allcurves}:{line_number}: expected six fields")
            try:
                ranks.add(int(fields[4]))
            except ValueError as error:
                raise ValueError(
                    f"{allcurves}:{line_number}: rank is not an integer"
                ) from error

    for source in rank_sources.iterdir():
        if source.is_file():
            ranks.add(_rank_number(source))
    return tuple(f"rank{rank}" for rank in sorted(ranks))


def create_rank_databases(
    allcurves: Path, rank_sources: Path, output_directory: Path
) -> tuple[Path, ...]:
    """Create text databases of elliptic curves grouped by rank."""
    names = rank_names(allcurves, rank_sources)
    output_directory.mkdir(parents=True, exist_ok=True)

    for stale in output_directory.glob("rank*"):
        if stale.is_file() and stale.name not in names:
            stale.unlink()

    outputs = tuple(output_directory / name for name in names)
    with ExitStack() as stack:
        destinations = {
            output.name: stack.enter_context(output.open("w", encoding="ascii"))
            for output in outputs
        }
        with allcurves.open(encoding="ascii") as source:
            for line in source:
                rank = "rank" + line.split()[4]
                destinations[rank].write(line)

        for source_path in sorted(rank_sources.iterdir(), key=_rank_number):
            if not source_path.is_file():
                continue
            with source_path.open(encoding="ascii") as source:
                destinations[source_path.name].write(source.read())
    return outputs


def generate(data_root: Path) -> None:
    """Generate all packaged resources below ``data_root``."""
    create_cremona_database(
        ALLCURVES, data_root / "cremona" / "cremona_mini.db"
    )
    create_rank_databases(ALLCURVES, RANK_SOURCES, data_root / "ellcurves")


def _schema(connection: sqlite3.Connection) -> list[tuple[str, ...]]:
    return connection.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        """
    ).fetchall()


def _compare_databases(expected: Path, actual: Path) -> None:
    if not actual.is_file():
        raise RuntimeError(f"committed database is missing: {actual}")
    actual_uri = f"{actual.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(expected) as expected_connection, sqlite3.connect(
        actual_uri, uri=True
    ) as actual_connection:
        if _schema(expected_connection) != _schema(actual_connection):
            raise RuntimeError(f"generated schema differs from {actual}")
        for table, key in (("t_class", "class"), ("t_curve", "curve")):
            query = f"SELECT * FROM {table} ORDER BY {key}"
            if expected_connection.execute(query).fetchall() != actual_connection.execute(
                query
            ).fetchall():
                raise RuntimeError(f"generated table {table} differs from {actual}")


def check() -> None:
    """Check committed resources against a fresh logical generation."""
    with tempfile.TemporaryDirectory(prefix="sage-data-elliptic-curves-") as tmp:
        generated = Path(tmp) / "data"
        generate(generated)
        _compare_databases(
            generated / "cremona" / "cremona_mini.db",
            DATA_ROOT / "cremona" / "cremona_mini.db",
        )

        generated_ranks = generated / "ellcurves"
        committed_ranks = DATA_ROOT / "ellcurves"
        generated_names = sorted(path.name for path in generated_ranks.glob("rank*"))
        committed_names = sorted(path.name for path in committed_ranks.glob("rank*"))
        if generated_names != committed_names:
            raise RuntimeError("committed rank-file manifest differs from generation")
        for name in generated_names:
            if (generated_ranks / name).read_bytes() != (
                committed_ranks / name
            ).read_bytes():
                raise RuntimeError(f"generated {name} differs from committed data")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify committed resources without modifying them",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        check()
    else:
        generate(DATA_ROOT)


if __name__ == "__main__":
    main()
