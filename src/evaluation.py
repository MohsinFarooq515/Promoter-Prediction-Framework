import json, math
from pathlib import Path
import numpy as np

def metrics(y,p,threshold=.5):
    from sklearn.metrics import accuracy_score,average_precision_score,balanced_accuracy_score,brier_score_loss,confusion_matrix,f1_score,matthews_corrcoef,precision_score,roc_auc_score
    y=np.asarray(y); p=np.asarray(p); pred=p>=threshold; tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel(); sensitivity=tp/max(tp+fn,1); specificity=tn/max(tn+fp,1)
    return {"accuracy":accuracy_score(y,pred),"sensitivity":sensitivity,"specificity":specificity,"precision":precision_score(y,pred,zero_division=0),"recall":sensitivity,"f1":f1_score(y,pred,zero_division=0),"mcc":matthews_corrcoef(y,pred),"balanced_accuracy":balanced_accuracy_score(y,pred),"roc_auc":roc_auc_score(y,p) if len(set(y))>1 else math.nan,"pr_auc":average_precision_score(y,p) if len(set(y))>1 else math.nan,"false_positive_rate":1-specificity,"false_negative_rate":1-sensitivity,"brier_score":brier_score_loss(y,p),"confusion_matrix":[[int(tn),int(fp)],[int(fn),int(tp)]]}

def select_threshold(y,p):
    y=np.asarray(y,dtype=np.int64); p=np.asarray(p,dtype=float)
    if len(y)==0 or not np.isfinite(p).all(): raise ValueError("threshold selection requires finite, non-empty validation predictions")
    order=np.argsort(-p,kind="stable"); ys=y[order]; ps=p[order]
    tp=np.cumsum(ys); fp=np.cumsum(1-ys); positives=tp[-1]; negatives=fp[-1]
    boundaries=np.r_[np.flatnonzero(ps[:-1] != ps[1:]),len(ps)-1]
    tp=tp[boundaries].astype(float); fp=fp[boundaries].astype(float); fn=positives-tp; tn=negatives-fp
    denominator=np.sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)); scores=np.divide(tp*tn-fp*fn,denominator,out=np.zeros_like(tp),where=denominator>0)
    thresholds=ps[boundaries]; best=np.flatnonzero(scores==scores.max()); chosen=best[np.argmin(np.abs(thresholds[best]-.5))]
    return float(thresholds[chosen])

def bootstrap_ci(y,p,threshold,n=1000,seed=2025):
    rng=np.random.default_rng(seed); y=np.asarray(y); p=np.asarray(p); vals={k:[] for k in ("mcc","roc_auc","pr_auc")}
    for _ in range(n):
        idx=rng.integers(0,len(y),len(y)); m=metrics(y[idx],p[idx],threshold)
        for k in vals:
            if not math.isnan(m[k]): vals[k].append(m[k])
    return {k:[float(np.quantile(v,.025)),float(np.quantile(v,.975))] for k,v in vals.items()}
