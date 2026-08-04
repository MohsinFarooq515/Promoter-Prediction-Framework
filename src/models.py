from __future__ import annotations
import math
import torch
from torch import nn

def masked_pool(x,mask):
    m=mask.unsqueeze(-1); mean=(x*m).sum(1)/m.sum(1).clamp_min(1)
    maximum=x.masked_fill(~m,torch.finfo(x.dtype).min).max(1).values
    maximum=torch.where(torch.isfinite(maximum),maximum,torch.zeros_like(maximum))
    return torch.cat([mean,maximum],-1)

class ResidualBlock(nn.Module):
    def __init__(self,c,k=5,dropout=.2):
        super().__init__(); self.net=nn.Sequential(nn.Conv1d(c,c,k,padding=k//2),nn.BatchNorm1d(c),nn.GELU(approximate="tanh"),nn.Dropout(dropout),nn.Conv1d(c,c,k,padding=k//2),nn.BatchNorm1d(c))
    def forward(self,x): return torch.nn.functional.gelu(x+self.net(x),approximate="tanh")

class ResidualCNN(nn.Module):
    def __init__(self,channels=64,blocks=3,kernel=5,dropout=.2,**_):
        super().__init__(); self.proj=nn.Conv1d(4,channels,7,padding=3); self.blocks=nn.Sequential(*[ResidualBlock(channels,kernel,dropout) for _ in range(blocks)]); self.head=nn.Sequential(nn.Dropout(dropout),nn.Linear(channels*2,1))
    def features(self,x,mask): return masked_pool(self.blocks(self.proj(x.transpose(1,2))).transpose(1,2),mask)
    def forward(self,x,mask,**_): return self.head(self.features(x,mask)).squeeze(-1)

class MultiScaleCNN(nn.Module):
    def __init__(self,channels=32,kernels=(3,5,7,11),blocks=2,hidden=128,dropout=.2,**_):
        super().__init__(); self.branches=nn.ModuleList([nn.Sequential(nn.Conv1d(4,channels,k,padding=k//2),nn.BatchNorm1d(channels),nn.GELU(approximate="tanh"),*[ResidualBlock(channels,k,dropout) for _ in range(blocks)]) for k in kernels]); self.project=nn.Linear(channels*len(kernels),hidden); self.head=nn.Sequential(nn.Dropout(dropout),nn.Linear(hidden*2,1))
    def sequence_features(self,x): return torch.nn.functional.gelu(self.project(torch.cat([b(x.transpose(1,2)).transpose(1,2) for b in self.branches],-1)),approximate="tanh")
    def forward(self,x,mask,**_): return self.head(masked_pool(self.sequence_features(x),mask)).squeeze(-1)

class CNNBiLSTM(nn.Module):
    def __init__(self,channels=64,hidden=96,layers=1,dropout=.2,**_):
        super().__init__(); self.conv=nn.Sequential(nn.Conv1d(4,channels,7,padding=3),nn.BatchNorm1d(channels),nn.GELU(approximate="tanh")); self.rnn=nn.LSTM(channels,hidden,layers,batch_first=True,bidirectional=True,dropout=dropout if layers>1 else 0); self.head=nn.Sequential(nn.Dropout(dropout),nn.Linear(hidden*4,1))
    def forward(self,x,mask,length=None,**_):
        z=self.conv(x.transpose(1,2)).transpose(1,2); lengths=mask.sum(1).cpu() if length is None else length.cpu()
        packed=nn.utils.rnn.pack_padded_sequence(z,lengths,batch_first=True,enforce_sorted=False); out,_=self.rnn(packed); out,_=nn.utils.rnn.pad_packed_sequence(out,batch_first=True,total_length=x.shape[1])
        return self.head(masked_pool(out,mask)).squeeze(-1)

class PositionalEncoding(nn.Module):
    def __init__(self,d,max_len=4096):
        super().__init__(); p=torch.arange(max_len).unsqueeze(1); div=torch.exp(torch.arange(0,d,2)*(-math.log(10000)/d)); pe=torch.zeros(max_len,d); pe[:,0::2]=torch.sin(p*div); pe[:,1::2]=torch.cos(p*div); self.register_buffer("pe",pe)
    def forward(self,x): return x+self.pe[:x.shape[1]]

class CNNTransformer(nn.Module):
    def __init__(self,hidden=96,heads=4,layers=2,ff_mult=3,dropout=.2,**_):
        super().__init__(); self.conv=nn.Sequential(nn.Conv1d(4,hidden,7,padding=3),nn.GELU(approximate="tanh")); self.pos=PositionalEncoding(hidden); layer=nn.TransformerEncoderLayer(hidden,heads,hidden*ff_mult,dropout,batch_first=True,norm_first=True,activation=lambda x: torch.nn.functional.gelu(x,approximate="tanh")); self.encoder=nn.TransformerEncoder(layer,layers); self.head=nn.Sequential(nn.Dropout(dropout),nn.Linear(hidden*2,1))
    def sequence_features(self,x,mask): return self.encoder(self.pos(self.conv(x.transpose(1,2)).transpose(1,2)),src_key_padding_mask=~mask)
    def forward(self,x,mask,**_): return self.head(masked_pool(self.sequence_features(x,mask),mask)).squeeze(-1)

class DomainAwareModel(nn.Module):
    def __init__(self,hidden=96,heads=4,layers=2,kernels=(3,5,7,11),dropout=.2,num_organisms=0,**_):
        super().__init__(); self.encoders=nn.ModuleList([nn.Conv1d(4,hidden,1) for _ in range(3)]); branch=max(8,hidden//len(kernels)); self.branches=nn.ModuleList([nn.Conv1d(hidden,branch,k,padding=k//2) for k in kernels]); self.fuse=nn.Linear(branch*len(kernels),hidden); self.embedding=nn.Embedding(3,hidden); self.pos=PositionalEncoding(hidden); layer=nn.TransformerEncoderLayer(hidden,heads,hidden*3,dropout,batch_first=True,norm_first=True,activation=lambda x: torch.nn.functional.gelu(x,approximate="tanh")); self.transformer=nn.TransformerEncoder(layer,layers); self.shared=nn.Linear(hidden*2,1); self.specialists=nn.ModuleList([nn.Linear(hidden*2,1) for _ in range(3)]); self.domain_head=nn.Linear(hidden*2,3); self.organism_head=nn.Linear(hidden*2,num_organisms) if num_organisms else None
    def forward(self,x,mask,domain,**_):
        z=torch.empty(x.shape[0],self.encoders[0].out_channels,x.shape[1],device=x.device)
        for d,enc in enumerate(self.encoders):
            idx=domain==d
            if idx.any(): z[idx]=enc(x[idx].transpose(1,2))
        z=torch.cat([torch.nn.functional.gelu(b(z),approximate="tanh").transpose(1,2) for b in self.branches],-1); z=self.fuse(z)+self.embedding(domain).unsqueeze(1); z=self.transformer(self.pos(z),src_key_padding_mask=~mask); pooled=masked_pool(z,mask)
        specialist=torch.empty(x.shape[0],device=x.device)
        for d,head in enumerate(self.specialists):
            idx=domain==d
            if idx.any(): specialist[idx]=head(pooled[idx]).squeeze(-1)
        return {"shared":self.shared(pooled).squeeze(-1),"specialist":specialist,"domain":self.domain_head(pooled),"organism":self.organism_head(pooled) if self.organism_head else None}

MODELS={"residual_cnn":ResidualCNN,"multiscale_cnn":MultiScaleCNN,"cnn_bilstm":CNNBiLSTM,"cnn_transformer":CNNTransformer,"domain_aware":DomainAwareModel}
