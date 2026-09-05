# Data provenance verification

Verified against the repository on 2026-08-14.

## Bacillus subtilis

The finalized files now match the correctly located B. subtilis CD-HIT outputs byte-for-byte:

| Class | Raw records | CD-HIT/finalized records | Finalized SHA-256 |
|---|---:|---:|---|
| Promoter | 766 | 675 | `b3ae7fcb1c04bd24df42ecf67d05279fc8e8357f1f3621ec2717488b2b83fb6b` |
| Non-promoter | 766 | 766 | `1ca13a341f60c8dcf7d7201a0ee34759ea220e465792771bbb98bc467ff734b2` |

The obsolete files under `data/2) cd-hit at 0.9/Archaeal/` contain 368/865 B. subtilis records and are not used by the training pipeline.

## Archaea

The repository contains 3,955 raw promoter records and 3,624 finalized promoter records, but no correctly labelled intermediate archaeal CD-HIT output. The finalized archaeal dataset is usable and audited, but the missing intermediate clustering artifact is a provenance limitation. It must not be represented as a fully reproducible raw-to-finalized transformation until the original clustering output or command log is recovered.

The archaeal non-promoter filename indicates genomic +21 to +121 regions. These are treated as genomic negative regions, not composition-preserving shuffled promoters.
