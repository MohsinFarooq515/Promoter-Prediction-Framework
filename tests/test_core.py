import csv
from pathlib import Path
import numpy as np, torch
from src.data import read_fasta,audit_file,one_hot,reverse_complement,Record,assign_splits
from src.evaluation import metrics,select_threshold
from src.models import MODELS
from src.groups import DOMAIN_GROUPS, model_group_for
from src.features import canonical, canonical_vocabulary, sequence_features

def test_fasta_duplicate_headers_and_lengths(tmp_path):
    p=tmp_path/"Archaeal_promoter.fasta"; p.write_text(">x\nACGT\n>x\nACG\n")
    assert len(read_fasta(p))==2; a=audit_file(p); assert a["duplicate_header_count"]==1 and a["equal_length"]=="No" and a["length_distribution"]=={3:1,4:1}
def test_encoding_n_and_padding():
    x,valid,pos=one_hot("AN",4); assert x.shape==(4,4) and valid.tolist()==[True,False,False,False] and pos.tolist()==[True,True,False,False]
def test_reverse_complement_group_split():
    def r(i,s,y): return Record(i,i,"f","archaea","Archaea_unspecified",y,s,len(s),4,.5,0)
    rows=[r("a","ACGT",0),r("b",reverse_complement("ACGT"),1)]; from src.data import canonical_group
    for x in rows:x.group_id=canonical_group(x.sequence)
    rows,c=assign_splits(rows); assert len(c)==1 and all(x.partition.startswith("quarantine") for x in rows)
def test_model_shapes():
    x=torch.randn(2,20,4); mask=torch.ones(2,20,dtype=torch.bool); domain=torch.tensor([0,2])
    for name,cls in MODELS.items():
        m=cls(hidden=32,channels=16,heads=4,layers=1,blocks=1); out=m(x,mask,length=torch.tensor([20,20]),domain=domain); assert (out["shared"] if isinstance(out,dict) else out).shape==(2,)
def test_threshold_and_metrics():
    y=np.array([0,0,1,1]); p=np.array([.1,.4,.6,.9]); t=select_threshold(y,p); assert metrics(y,p,t)["mcc"]==1
def test_organism_model_groups():
    assert DOMAIN_GROUPS["bacteria"] == ("ecoli", "bsubtilis")
    assert set(DOMAIN_GROUPS["eukaryota"]) == {"human", "mouse", "arabidopsis"}
    assert model_group_for("Bacillus subtilis") == "bsubtilis"
def test_canonical_kmers_collapse_reverse_complements():
    assert canonical("ATGCGA") == canonical("TCGCAT")
    assert len(canonical_vocabulary(6)) < sum(4**k for k in range(1,7))
def test_feature_blocks_and_no_n_ratio():
    base=sequence_features("A"*80,81,"bacteria",("canonical_kmers",))
    positioned=sequence_features("A"*80,81,"bacteria",("canonical_kmers","position_specific"))
    stable=sequence_features("A"*80,81,"bacteria",("canonical_kmers","stability"))
    assert len(positioned)>len(base) and len(stable)==len(base)+5
