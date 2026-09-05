from __future__ import annotations

from functools import lru_cache
from itertools import product

import numpy as np

ALPHABET = "ACGT"
COMPLEMENT = str.maketrans("ACGT", "TGCA")
DEFAULT_BLOCKS = ("canonical_kmers", "position_specific", "stability")

# SantaLucia nearest-neighbour duplex delta-G at 37 C (kcal/mol).
DINUCLEOTIDE_DG37 = {
    "AA": -1.00, "TT": -1.00, "AT": -0.88, "TA": -0.58,
    "CA": -1.45, "TG": -1.45, "GT": -1.44, "AC": -1.44,
    "CT": -1.28, "AG": -1.28, "GA": -1.30, "TC": -1.30,
    "CG": -2.17, "GC": -2.24, "GG": -1.84, "CC": -1.84,
}


def reverse_complement(sequence: str) -> str:
    return sequence.translate(COMPLEMENT)[::-1]


def canonical(kmer: str) -> str:
    return min(kmer, reverse_complement(kmer))


@lru_cache(maxsize=None)
def canonical_vocabulary(max_k: int = 6):
    vocab = []
    for k in range(1, max_k + 1):
        vocab.extend(sorted({canonical("".join(chars)) for chars in product(ALPHABET, repeat=k)}))
    return tuple(vocab)


@lru_cache(maxsize=None)
def canonical_index(max_k: int = 6):
    return {word: index for index, word in enumerate(canonical_vocabulary(max_k))}


@lru_cache(maxsize=None)
def canonical_lookup(max_k: int = 6):
    index=canonical_index(max_k)
    return {word:index[canonical(word)] for k in range(1,max_k+1)
            for word in ("".join(chars) for chars in product(ALPHABET,repeat=k))}


@lru_cache(maxsize=None)
def kmer_slices(max_k: int = 6):
    vocabulary=canonical_vocabulary(max_k); out={}; cursor=0
    for k in range(1,max_k+1):
        size=sum(len(word)==k for word in vocabulary); out[k]=(cursor,cursor+size); cursor+=size
    return out


def _normalized_kmers(sequence: str, max_k: int) -> np.ndarray:
    index=canonical_index(max_k); lookup=canonical_lookup(max_k); offsets=kmer_slices(max_k)
    values = np.zeros(len(index), dtype=np.float32)
    for k in range(1, max_k + 1):
        valid = 0
        for start in range(len(sequence) - k + 1):
            word = sequence[start:start + k]
            if word in lookup:
                values[lookup[word]] += 1
                valid += 1
        if valid:
            begin, end = offsets[k]
            values[begin:end] /= valid
    return values


def _directional_kmers(sequence: str, minimum_k: int, maximum_k: int) -> np.ndarray:
    """Normalized strand-aware k-mers for transcription-orientation-aligned records."""
    pieces=[]
    for k in range(minimum_k,maximum_k+1):
        words=("".join(chars) for chars in product(ALPHABET,repeat=k))
        index={word:i for i,word in enumerate(words)}
        values=np.zeros(4**k,dtype=np.float32); valid=0
        for start in range(len(sequence)-k+1):
            word=sequence[start:start+k]
            if word in index: values[index[word]]+=1; valid+=1
        if valid: values/=valid
        pieces.append(values)
    return np.concatenate(pieces)


def _legacy_kmers(sequence: str) -> np.ndarray:
    """Original directional 1-4-mer block, retained as the ablation baseline."""
    return _directional_kmers(sequence,1,4)


def _composition(sequence: str, maximum_length: int) -> np.ndarray:
    valid=sum(base in ALPHABET for base in sequence)
    # N-ratio deliberately removed: it is constant in the finalized data.
    return np.asarray([len(sequence)/maximum_length,
        (sequence.count("G")+sequence.count("C"))/max(valid,1),
        abs(sequence.count("G")-sequence.count("C"))/max(valid,1)],dtype=np.float32)


def _coarse_position(sequence: str) -> np.ndarray:
    values=np.zeros(40,dtype=np.float32)
    for position,base in enumerate(sequence):
        if base in ALPHABET:
            bin_index=min(9,position*10//max(len(sequence),1)); values[bin_index*4+ALPHABET.index(base)]+=1
    for bin_index in range(10):
        block=values[bin_index*4:(bin_index+1)*4]; total=block.sum()
        if total: block/=total
    return values


def position_windows(domain: str, sequence_length: int):
    if domain == "bacteria":
        # Bacterial records are treated as starting at -60; bounds are half-open.
        tss=60
        return (("minus35",tss-42,tss-27),("minus10",tss-17,tss-2))
    if domain == "eukaryota":
        # Headers document -200..+50, so the TSS is index 200.
        tss=200
        return (("upstream_tss",tss-50,tss),("core_tss",tss-10,tss+11),("downstream_tss",tss,tss+51))
    return ()


def _position_specific(sequence: str, domain: str) -> np.ndarray:
    pieces=[]
    for _,start,end in position_windows(domain,len(sequence)):
        window=sequence[max(0,start):min(len(sequence),end)]
        pieces.append(_normalized_kmers(window,3))
    return np.concatenate(pieces) if pieces else np.empty(0,dtype=np.float32)


def _stability(sequence: str) -> np.ndarray:
    energies=np.asarray([DINUCLEOTIDE_DG37[sequence[i:i+2]] for i in range(len(sequence)-1)
                         if sequence[i:i+2] in DINUCLEOTIDE_DG37],dtype=np.float32)
    if not len(energies): return np.zeros(5,dtype=np.float32)
    return np.asarray([energies.sum(),energies.mean(),energies.std(),
                       energies.min(),energies.max()],dtype=np.float32)


def sequence_features(sequence: str, maximum_length: int, domain: str = "bacteria",
                      blocks=DEFAULT_BLOCKS) -> np.ndarray:
    """Build independently switchable feature blocks for validation ablation."""
    sequence=sequence.upper(); blocks=tuple(blocks)
    if "directional_kmers_1_6" in blocks: kmer_block=_directional_kmers(sequence,1,6)
    elif "directional_kmers_3_6" in blocks: kmer_block=_directional_kmers(sequence,3,6)
    elif "legacy_kmers" in blocks: kmer_block=_legacy_kmers(sequence)
    else: kmer_block=_normalized_kmers(sequence,6)
    pieces=[kmer_block,
            _composition(sequence,maximum_length),_coarse_position(sequence)]
    if "position_specific" in blocks: pieces.append(_position_specific(sequence,domain))
    if "stability" in blocks: pieces.append(_stability(sequence))
    return np.concatenate(pieces).astype(np.float32,copy=False)


def feature_matrix(sequences, maximum_length: int, domain: str = "bacteria", blocks=DEFAULT_BLOCKS) -> np.ndarray:
    return np.stack([sequence_features(sequence,maximum_length,domain,blocks) for sequence in sequences])
