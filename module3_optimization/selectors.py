"""Frozen objective rules. No resource-cost or hidden recovery-floor objective."""
import numpy as np
from module2_prediction.validation import numeric

def select_modes(predictions, supported, floors=(95,90), joint_rule='distance'):
    y=np.asarray(predictions,float); support=np.asarray(supported,bool)
    f=np.array([numeric(v,'최소치') for v in floors])
    if y.ndim!=2 or y.shape[1]!=2 or support.shape!=(len(y),) or f.shape!=(2,):
        raise ValueError('선택 함수의 입력 형태가 잘못됐습니다.')
    if ((f<0)|(f>100)).any() or joint_rule not in ('distance','maximin'):
        raise ValueError('최소치는 0~100%, 공동 기준은 distance/maximin입니다.')
    physical=np.isfinite(y).all(1)&(y>=0).all(1)&(y<=100).all(1)
    valid=physical&support; result={}
    for mode in ('joint','ni','co'):
        meets=(y>=f).all(1) if mode=='joint' else np.ones(len(y),bool)
        def key(i):
            n,c=y[i]
            if mode=='ni': return (-n,-c,int(i))
            if mode=='co': return (-c,-n,int(i))
            if joint_rule=='maximin': return (-min(n,c),-(n+c),int(i))
            return ((100-n)**2+(100-c)**2,-min(n,c),int(i))
        ranked=sorted(map(int,np.flatnonzero(valid&meets)),key=key)
        best=ranked[0] if ranked else None
        before=int((physical&meets).sum())
        if best is not None: status='RECOMMENDED_ON_PREDICTION'
        elif not physical.any(): status='NO_VALID_MODEL_OUTPUT'
        elif not valid.any(): status='NO_SUPPORTED_CANDIDATE'
        elif mode=='joint' and before: status='TARGET_FOUND_BUT_UNSUPPORTED'
        else: status='TARGET_NOT_FOUND_IN_GRID'
        alt=None
        if best is None and mode=='joint' and valid.any():
            gap=np.maximum(f-y,0).sum(1)
            alt=int(min(np.flatnonzero(valid),key=lambda i:(gap[i],*key(i))))
        result[mode]=dict(index=best,ranked_indices=ranked[:3],status=status,
            eligible_count=len(ranked),raw_feasible=before,
            unsupported_feasible=int((physical&meets&~support).sum()),
            alternative_index=alt)
    return result
