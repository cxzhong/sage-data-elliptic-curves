from __future__ import annotations

import sqlite3

import pytest

from sage_data_elliptic_curves import (
    EllipticCurveRecord,
    available_ranks,
    cremona_mini_connection,
    cremona_mini_path,
    cremona_mini_resource,
    iter_rank,
    rank_path,
    rank_resource,
)


EXPECTED_RANKS = (
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    14,
    15,
    17,
    19,
    20,
    21,
    22,
    23,
    24,
    28,
)


def test_resource_manifest() -> None:
    assert cremona_mini_resource().is_file()
    assert available_ranks() == EXPECTED_RANKS
    assert all(rank_resource(rank).is_file() for rank in EXPECTED_RANKS)


def test_resource_paths() -> None:
    with cremona_mini_path() as path:
        assert path.is_file()
        assert path.name == "cremona_mini.db"
    with rank_path(28) as path:
        assert path.is_file()
        assert path.name == "rank28"


def test_cremona_database_contents_and_read_only_mode() -> None:
    with cremona_mini_connection() as connection:
        assert connection.execute("PRAGMA query_only").fetchone() == (1,)
        assert connection.execute("SELECT COUNT(*) FROM t_class").fetchone() == (
            38_042,
        )
        assert connection.execute("SELECT COUNT(*) FROM t_curve").fetchone() == (
            64_687,
        )
        assert connection.execute(
            "SELECT class, rank, conductor FROM t_class WHERE class = '11a'"
        ).fetchone() == ("11a", 0, 11)
        assert connection.execute(
            "SELECT curve, class, tors, eqn FROM t_curve WHERE curve = '11a1'"
        ).fetchone() == ("11a1", "11a", 5, "[0,-1,1,-10,-20]")
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM t_curve WHERE curve = '11a1'")


def test_iter_rank_returns_typed_records() -> None:
    first = next(iter_rank(3))
    assert first == EllipticCurveRecord(
        conductor=5_077,
        isogeny_class="a",
        number=1,
        ainvs=(0, 0, 1, -7, 6),
        rank=3,
        torsion_order=1,
    )
    assert first.class_label == "5077a"
    assert first.label == "5077a1"


@pytest.mark.parametrize("rank", [-1, 13, 16, 29])
def test_unavailable_rank(rank: int) -> None:
    error = ValueError if rank < 0 else FileNotFoundError
    with pytest.raises(error):
        rank_resource(rank)


@pytest.mark.parametrize("rank", [True, 3.0, "3", None])
def test_rank_must_be_an_integer(rank: object) -> None:
    with pytest.raises(TypeError):
        rank_resource(rank)  # type: ignore[arg-type]
