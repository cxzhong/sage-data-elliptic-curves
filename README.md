# sage-data-elliptic-curves

`sage-data-elliptic-curves` packages two small, read-only elliptic-curve
databases historically distributed as SageMath's `elliptic_curves` package:

- John Cremona's elliptic curves of conductor below 10,000, represented as a
  compact SQLite database; and
- William Stein's collection of interesting elliptic curves, combined with the
  Cremona records and grouped into text files by rank.

The package has no dependency on SageMath.  It exposes the data through
`importlib.resources`, so consumers do not need to know where the wheel was
installed.

> [!IMPORTANT]
> The legacy Sage distribution labels these datasets only as `None (database)`
> in `COPYING.txt`; the source archive does not contain a data-specific license.
> The exact license and redistribution terms must be confirmed with SageMath
> upstream and the named data authors before the first public PyPI release.
> See [DATA_LICENSES.md](https://github.com/cxzhong/sage-data-elliptic-curves/blob/main/DATA_LICENSES.md).

## Install

```console
python -m pip install sage-data-elliptic-curves
```

## Use

```python
from sage_data_elliptic_curves import (
    available_ranks,
    cremona_mini_connection,
    iter_rank,
)

print(available_ranks())

record = next(iter_rank(3))
print(record.label, record.ainvs)

with cremona_mini_connection() as connection:
    row = connection.execute(
        "SELECT curve, eqn FROM t_curve WHERE curve = ?", ("11a1",)
    ).fetchone()
    print(row)
```

`cremona_mini_resource()` and `rank_resource(rank)` return standard
`importlib.resources` traversables.  For APIs that require filesystem paths,
use the `cremona_mini_path()` and `rank_path(rank)` context managers; their
paths are valid only while the corresponding context is active.

## Regenerate the packaged data

The unmodified legacy inputs are retained under `sources/`.  Regenerate all
derived resources with:

```console
python generate.py
```

Check that the committed resources are logically identical to a fresh
generation without modifying them:

```console
python generate.py --check
```

The SQLite comparison is logical rather than byte-for-byte because SQLite file
layout can vary across SQLite releases.

## Develop

```console
python -m pip install -e '.[test]'
python generate.py --check
python -m pytest
python -m build
```

After the data terms are confirmed, publishing is performed only by the
`Release` GitHub Actions workflow when a GitHub Release is published.  The
workflow builds and checks both distributions, attaches them to that Release,
and uses PyPI Trusted Publishing through the protected `pypi` environment.
