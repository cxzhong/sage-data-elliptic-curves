# Data provenance and licensing status

This distribution contains two datasets copied from the legacy SageMath
`elliptic_curves` source archive version 0.8.1.

| Packaged resource | Legacy input | Credited author | Upstream reference |
| --- | --- | --- | --- |
| `data/cremona/cremona_mini.db` | `sources/common/allcurves.00000-09999` | John Cremona | <https://github.com/JohnCremona/ecdata> |
| `data/ellcurves/rank*` | the same Cremona input plus `sources/ellcurves/rank*` | John Cremona and William Stein | SageMath legacy `elliptic_curves` package |

## Unresolved data terms

SageMath's historical `COPYING.txt` table records `elliptic_curves` as
`None (database)`.  That entry is a description, not an SPDX license grant.
The 0.8.1 source archive itself contains no `LICENSE`, `COPYING`, or other
data-specific licensing notice.

Consequently, this repository does **not** claim that the GPL license in
`LICENSE` automatically covers the database contents.  That license covers the
original packaging and access code in this repository.  Before a public PyPI
release, SageMath upstream and the named data authors should confirm, in
writing, the applicable license, attribution requirements, and permission to
redistribute both the source records and generated SQLite/text forms.  This
file should then be updated with the confirmed terms and primary references.
