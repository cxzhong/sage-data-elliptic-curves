from __future__ import annotations

import sqlite3
from pathlib import Path

import generate


def test_fresh_generation(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    generate.generate(data_root)

    with sqlite3.connect(data_root / "cremona" / "cremona_mini.db") as connection:
        assert connection.execute("SELECT COUNT(*) FROM t_class").fetchone() == (
            38_042,
        )
        assert connection.execute("SELECT COUNT(*) FROM t_curve").fetchone() == (
            64_687,
        )

    rank_files = sorted(
        (path.name for path in (data_root / "ellcurves").iterdir()),
        key=lambda name: int(name.removeprefix("rank")),
    )
    assert len(rank_files) == 23
    assert rank_files[:4] == ["rank0", "rank1", "rank2", "rank3"]
    assert rank_files[-1] == "rank28"


def test_committed_generation_is_current() -> None:
    generate.check()
