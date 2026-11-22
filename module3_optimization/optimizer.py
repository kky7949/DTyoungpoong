"""Exhaustive grid recommendation, exact final coursework policy."""
import math
from decimal import Decimal
from itertools import product
from collections.abc import Mapping
import numpy as np
from module2_prediction.inference import Engine as PredictionEngine, FEATURES,CONTROLS,LIMITS,APP_VERSION,MODEL_VERSION
from module2_prediction.validation import numeric
from .selectors import select_modes


class Engine(PredictionEngine):
    def compare(self, values, ni_min=95, co_min=90, joint_rule='distance', grid=None):
        floors=(numeric(ni_min,'Ni 최소치'),numeric(co_min,'Co 최소치'))
        if any(not 0<=v<=100 for v in floors): raise ValueError('최소치는 0~100%입니다.')
        if joint_rule not in ('distance','maximin'): raise ValueError('공동 기준 오류')
        current=self.input_vector(values)
        if grid is None:
            grid=dict(zip(CONTROLS,(range(400,1501,50),range(40,96,5),np.arange(1,8.01,.5))))
        if not isinstance(grid,Mapping) or set(grid)!=set(CONTROLS):
            raise ValueError('격자는 황산량·온도·시간 3개를 지정하세요.')
        axes=[]
        for j,k in enumerate(CONTROLS,8):
            vals=grid[k]
            if isinstance(vals,(str,bytes)) or not hasattr(vals,'__len__') or not 1<=len(vals)<=50000:
                raise ValueError(f'{k}: 빈 격자 또는 너무 많은 후보입니다.')
            axis=sorted(set(numeric(v,k) for v in vals))
            if axis[0]<LIMITS[j,0] or axis[-1]>LIMITS[j,1]:
                raise ValueError(f'{k}: 지원 범위 밖입니다.')
            axes.append(axis)
        if math.prod(map(len,axes))>50000: raise ValueError('전체 후보는 50,000개 이하로 설정하세요.')
        c=np.array(list(product(*axes)),float)
        x=np.tile(current,(len(c),1));x[:,8:]=c
        y,d=self.calculate(x);support=np.isfinite(d)&(d<=self.threshold)
        physical=np.isfinite(y).all(1)&(y>=0).all(1)&(y<=100).all(1)
        valid=physical&support; baseline=self.predict(values)
        modes=select_modes(y,support,floors,joint_rule)
        for mode,info in modes.items():
            def describe(i):
                if i is None: return None
                out=self.row(x[i],y[i],d[i]);out['candidate_id']=int(i)
                out['margin_pp']=dict(zip(('Ni','Co'),map(float,y[i]-floors))) if mode=='joint' else None
                return out
            info['recommendation']=describe(info['index'])
            info['closest_alternative']=describe(info['alternative_index'])
            info['top_candidates']=[describe(i) for i in info['ranked_indices']]
        ids=[modes[k]['index'] for k in modes]
        return dict(app_version=APP_VERSION,model_version=MODEL_VERSION,
            evaluation_scope='영풍 제공 데이터 내부 검증; 독립 성능·실제 달성 보장 아님',
            current=baseline,modes=modes,candidate_count=len(x),valid_count=int(valid.sum()),
            output_rejected=int((~physical).sum()),distance_rejected=int((physical&~support).sum()),
            floors_pct=list(floors),joint_rule=joint_rule,
            supported_max_pct={m:float(y[valid,j].max()) if valid.any() else None
                               for j,m in enumerate(('Ni','Co'))},
            same_candidate_all=None not in ids and len(set(ids))==1,
            plant_operation_approved=False)


def make_axis(lo, hi, step, limits):
    a,b,s=[Decimal(str(numeric(v,'탐색 설정'))) for v in (lo,hi,step)]
    lower,upper=map(lambda v:Decimal(str(v)),limits)
    if not lower<=a<=b<=upper or s<=0: raise ValueError('탐색 범위·간격을 확인하세요.')
    count=int((b-a)//s)
    if count>49999: raise ValueError('탐색 간격이 너무 작습니다.')
    axis=[float(a+i*s) for i in range(count+1)]
    if a+count*s<b: axis.append(float(b))
    return axis
