from __future__ import annotations

import csv, hashlib, json, random, re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean, median, pstdev
from .groups import model_group_for

FASTA_EXTENSIONS = {".fasta", ".fa", ".fna", ".fas"}
COMPLEMENT = str.maketrans("ACGTN", "TGCAN")

@dataclass
class Record:
    internal_id: str; original_header: str; source_file: str; domain: str
    organism: str; label: int; sequence: str; original_length: int
    model_input_length: int; gc_content: float; ambiguity_count: int
    group_id: str = ""; partition: str = ""

def read_fasta(path):
    records=[]; header=None; chunks=[]
    with Path(path).open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            line=raw.strip()
            if not line: continue
            if line.startswith(">"):
                if header is not None: records.append((header, "".join(chunks).upper()))
                header=line[1:]; chunks=[]
            elif header is None: raise ValueError(f"{path}:{line_no}: sequence before FASTA header")
            else: chunks.append(re.sub(r"\s+", "", line))
    if header is not None: records.append((header, "".join(chunks).upper()))
    if not records: raise ValueError(f"{path}: no FASTA records")
    return records

def infer_metadata(path):
    text=str(path).lower(); name=Path(path).name.lower()
    if "archae" in text: domain, organism="archaea", "Archaea_unspecified"
    elif "eukary" in text:
        domain="eukaryota"
        if "mouse" in text: organism="Mus musculus"
        elif "human" in text: organism="Homo sapiens"
        elif "arabidopsis" in text: organism="Arabidopsis thaliana"
        else: raise ValueError(f"Cannot infer eukaryotic organism: {path}")
    elif "prokary" in text:
        domain="bacteria"
        if "bsub" in text or "subtilis" in text: organism="Bacillus subtilis"
        elif "ecoli" in text or "e. coli" in text: organism="Escherichia coli"
        else: raise ValueError(f"Cannot infer bacterial organism: {path}")
    else: raise ValueError(f"Cannot infer domain: {path}")
    if "non_promoter" in name or "non-promoter" in name: label=0
    elif "promoter" in name: label=1
    else: raise ValueError(f"Cannot infer class: {path}")
    return domain, organism, label

def reverse_complement(sequence): return sequence.translate(COMPLEMENT)[::-1]
def canonical_group(sequence):
    canonical=min(sequence, reverse_complement(sequence))
    return hashlib.sha256(canonical.encode()).hexdigest()[:20]

def audit_file(path):
    recs=read_fasta(path); headers=Counter(h for h,_ in recs); seqs=Counter(s for _,s in recs)
    lengths=Counter(map(len, (s for _,s in recs))); gc=[]; invalid=Counter()
    for _,seq in recs:
        invalid.update(c for c in seq if c not in "ACGTN")
        valid=sum(seq.count(c) for c in "ACGT")
        gc.append((seq.count("G")+seq.count("C"))/valid if valid else 0.0)
    domain,organism,label=infer_metadata(path)
    return {"file":str(path),"domain":domain,"organism":organism,"class":"promoter" if label else "non-promoter",
      "sequence_count":len(recs),"unique_sequence_count":len(seqs),"unique_header_count":len(headers),
      "duplicate_header_count":sum(v-1 for v in headers.values()),"exact_duplicate_sequence_count":sum(v-1 for v in seqs.values()),
      "minimum_length":min(lengths),"maximum_length":max(lengths),"mean_length":fmean(lengths.elements()),
      "median_length":median(lengths.elements()),"length_distribution":dict(sorted(lengths.items())),
      "equal_length":"Yes" if len(lengths)==1 else "No","invalid_characters":dict(invalid),
      "sequences_containing_n":sum("N" in s for _,s in recs),"empty_sequence_count":sum(not s for _,s in recs),
      "mean_gc":fmean(gc),"gc_std":pstdev(gc),"sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest()}

def discover(data_dir): return sorted(p for p in Path(data_dir).rglob("*") if p.suffix.lower() in FASTA_EXTENSIONS)

def build_records(data_dir):
    files=discover(data_dir); audits=[audit_file(p) for p in files]
    domain_lengths={d:max(a["maximum_length"] for a in audits if a["domain"]==d) for d in {a["domain"] for a in audits}}
    out=[]
    for path in files:
        domain,organism,label=infer_metadata(path)
        for index,(header,seq) in enumerate(read_fasta(path),1):
            digest=hashlib.sha256(f"{path}|{index}|{header}|{seq}".encode()).hexdigest()[:20]
            valid=sum(seq.count(c) for c in "ACGT"); gc=(seq.count("G")+seq.count("C"))/valid if valid else 0
            out.append(Record(f"seq_{digest}",header,str(path),domain,organism,label,seq,len(seq),domain_lengths[domain],gc,seq.count("N"),canonical_group(seq)))
    return out,audits,domain_lengths

def assign_splits(records, seed=2025, fractions=(.70,.15,.15)):
    labels_by_group=defaultdict(set)
    for r in records: labels_by_group[(r.domain,r.group_id)].add(r.label)
    conflicts={key for key,labels in labels_by_group.items() if len(labels)>1}
    for r in records:
        if (r.domain,r.group_id) in conflicts: r.partition="quarantine_reverse_complement_conflict"
    rng=random.Random(seed)
    strata=defaultdict(list)
    for r in records:
        if not r.partition: strata[(r.domain,r.organism,r.label)].append(r)
    for items in strata.values():
        groups=defaultdict(list)
        for r in items: groups[r.group_id].append(r)
        grouped=list(groups.values()); rng.shuffle(grouped); total=sum(map(len,grouped)); targets=[fractions[0]*total,(fractions[0]+fractions[1])*total]
        count=0
        for group in grouped:
            part="train" if count < targets[0] else ("validation" if count < targets[1] else "test")
            for r in group: r.partition=part
            count += len(group)
    return records, conflicts

def write_manifest(records,path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fields=["internal_id","original_header","source_file","domain","organism","model_group","class","original_length","model_input_length","group_id","partition"]
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in records:
            d=asdict(r); d["model_group"]=model_group_for(r.organism); d["class"]="promoter" if r.label else "non-promoter"; w.writerow({k:d[k] for k in fields})

def one_hot(sequence,max_length):
    import torch
    if len(sequence)>max_length: raise ValueError(f"sequence length {len(sequence)} exceeds {max_length}")
    x=torch.zeros(max_length,4); valid=torch.zeros(max_length,dtype=torch.bool)
    for i,c in enumerate(sequence):
        if c in "ACGT": x[i,"ACGT".index(c)]=1; valid[i]=True
        elif c != "N": raise ValueError(f"invalid nucleotide {c!r}")
    position=torch.zeros(max_length,dtype=torch.bool); position[:len(sequence)]=True
    return x,valid,position

class SequenceDataset:
    def __init__(self,records): self.records=records
    def __len__(self): return len(self.records)
    def __getitem__(self,i):
        r=self.records[i]; x,valid,position=one_hot(r.sequence,r.model_input_length)
        return {"x":x,"valid_mask":valid,"position_mask":position,"length":r.original_length,"label":r.label,"domain":{"bacteria":0,"archaea":1,"eukaryota":2}[r.domain],"id":r.internal_id}
