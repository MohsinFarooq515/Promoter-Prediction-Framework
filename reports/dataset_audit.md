# Dataset audit

Finalized source: `data/3) finalized`. Original FASTA files were read only.

| File | Domain | Organism | Class | Sequence Count | Minimum Length | Maximum Length | Length Distribution | Equal Length |
|---|---|---|---|---:|---:|---:|---|---|
| data\3) finalized\Archaeal\Archaeal_non_promoter.fasta | archaea | Archaea_unspecified | non-promoter | 6992 | 100 | 100 | 100 nt: 6992 sequences | Yes |
| data\3) finalized\Archaeal\Archaeal_promoter.fasta | archaea | Archaea_unspecified | promoter | 3624 | 100 | 100 | 100 nt: 3624 sequences | Yes |
| data\3) finalized\Eukaryotic Species\Animal\Mouse_non_promoter.fasta | eukaryota | Mus musculus | non-promoter | 23291 | 251 | 251 | 251 nt: 23291 sequences | Yes |
| data\3) finalized\Eukaryotic Species\Animal\Mouse_promoter.fasta | eukaryota | Mus musculus | promoter | 16110 | 251 | 251 | 251 nt: 16110 sequences | Yes |
| data\3) finalized\Eukaryotic Species\Human\Human_non_promoter.fasta | eukaryota | Homo sapiens | non-promoter | 12943 | 251 | 251 | 251 nt: 12943 sequences | Yes |
| data\3) finalized\Eukaryotic Species\Human\Human_promoter.fasta | eukaryota | Homo sapiens | promoter | 19596 | 251 | 251 | 251 nt: 19596 sequences | Yes |
| data\3) finalized\Eukaryotic Species\Plant\Arabidopsis_non_promoter.fasta | eukaryota | Arabidopsis thaliana | non-promoter | 2866 | 251 | 251 | 251 nt: 2866 sequences | Yes |
| data\3) finalized\Eukaryotic Species\Plant\Arabidopsis_promoter.fasta | eukaryota | Arabidopsis thaliana | promoter | 5885 | 251 | 251 | 251 nt: 5885 sequences | Yes |
| data\3) finalized\Prokaryotic Species\B. Subtilis\Bsub_non_promoter.fasta | bacteria | Bacillus subtilis | non-promoter | 766 | 80 | 80 | 80 nt: 766 sequences | Yes |
| data\3) finalized\Prokaryotic Species\B. Subtilis\Bsub_promoter.fasta | bacteria | Bacillus subtilis | promoter | 675 | 80 | 80 | 80 nt: 675 sequences | Yes |
| data\3) finalized\Prokaryotic Species\E. coli\Ecoli_non_promoter.fasta | bacteria | Escherichia coli | non-promoter | 3369 | 81 | 81 | 81 nt: 3369 sequences | Yes |
| data\3) finalized\Prokaryotic Species\E. coli\Ecoli_promoter.fasta | bacteria | Escherichia coli | promoter | 3204 | 81 | 81 | 81 nt: 3204 sequences | Yes |

## Decisions
- Domain input lengths: {'eukaryota': 251, 'archaea': 100, 'bacteria': 81}.
- Reverse-complement cross-label conflict groups quarantined: 6 (12 records).
- Exact duplicates and reverse complements share a deterministic group ID and cannot cross partitions.
- `N` is encoded as zeros with a separate validity mask; padding uses zeros with a position mask.
- Full statistics and SHA-256 hashes are in `results/main_tables/dataset_audit.json`.
