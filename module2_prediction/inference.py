"""Fixed-state prediction. This module never fits a model or reads RAW data."""
import json
from pathlib import Path
from collections.abc import Mapping
import numpy as np
from module1_preprocessing.schema import BASE as FEATURES, LIMITS as INPUT_LIMITS
from module1_preprocessing.features import feature_matrix
from .validation import numeric

CONTROLS=FEATURES[8:]
LIMITS=np.array([INPUT_LIMITS[k] for k in FEATURES],float)
APP_VERSION='YP-course-final-1.0'
MODEL_VERSION='YP-curve17-dev357-v2'
SOURCE_CODE_SHA256='c060f5e49a1feb5f3f3bff0705ca49e3c96ef3c4a8217f2c337eb2644616e9b8'


class Engine:
    def __init__(self, model_path=None):
        path=Path(model_path) if model_path is not None else Path(__file__).parent/'artifacts/frozen_model.json'
        state=json.loads(path.read_text(encoding='utf-8'))
        if (state.get('model_version')!=MODEL_VERSION or state.get('fit_rows')!=357
            or state.get('app_version',APP_VERSION)!=APP_VERSION
            or state.get('source_code_sha256',SOURCE_CODE_SHA256)!=SOURCE_CODE_SHA256):
            raise ValueError('모델 메타데이터가 최종 357행 모델과 일치하지 않습니다.')
        if state.get('features') != list(FEATURES):
            raise ValueError('모델 입력 변수 순서가 맞지 않습니다.')
        self.parameters=np.array(state['parameters'],dtype=float)
        self.dm=np.array(state['distance_mean'],dtype=float)
        self.ds=np.array(state['distance_scale'],dtype=float)
        self.points=np.array(state['distance_points'],dtype=float)
        self.threshold=numeric(state['distance_threshold'],'거리 기준')
        if (self.parameters.shape!=(2,52) or self.dm.shape!=(11,) or self.ds.shape!=(11,)
            or self.points.ndim!=2 or self.points.shape[1]!=11 or len(self.points)<2
            or not all(np.isfinite(a).all() for a in (self.parameters,self.dm,self.ds,self.points))
            or (self.ds<=0).any() or (self.parameters[:,17:34]<=0).any() or self.threshold<=0):
            raise ValueError('저장된 모델 수치의 형태 또는 범위가 잘못됐습니다.')
        self.reference=np.ascontiguousarray((self.points-self.dm)/self.ds)
        for a in (self.parameters,self.dm,self.ds,self.points,self.reference):
            a.flags.writeable=False

    def input_vector(self, values):
        if not isinstance(values,Mapping) or set(values)!=set(FEATURES):
            raise ValueError('11개 입력 항목이 모두 필요합니다.')
        x=np.array([numeric(values[k],k) for k in FEATURES])
        bad=(x<LIMITS[:,0])|(x>LIMITS[:,1])
        if bad.any():
            i=int(np.flatnonzero(bad)[0]);lo,hi=LIMITS[i]
            raise ValueError(f'{FEATURES[i]}: 지원 범위 {lo:g}~{hi:g}')
        if x[:7].sum()>100: raise ValueError('원료 성분 합계가 100 wt%를 넘습니다.')
        return x

    def calculate(self, x):
        x=np.asarray(x,float)
        if x.ndim!=2 or x.shape[1]!=11 or not np.isfinite(x).all():
            raise ValueError('계산 입력은 유한한 숫자 11개로 구성해야 합니다.')
        z=feature_matrix(x,'A17')
        y=np.column_stack([((z-p[:17])/p[17:34])@p[34:51]+p[51]
                           for p in self.parameters])
        distance=np.empty(len(x));q=(x-self.dm)/self.ds
        for start in range(0,len(x),256):
            d=q[start:start+256,None,:]-self.reference[None,:,:]
            distance[start:start+256]=np.sqrt((d*d).sum(2).min(1))
        return y,distance

    def row(self, x, y, distance):
        flags=[]
        if not np.isfinite(y).all(): flags.append('NONFINITE_OUTPUT')
        elif ((y<0)|(y>100)).any(): flags.append('OUTPUT_OUT_OF_RANGE')
        if not np.isfinite(distance) or distance>self.threshold:
            flags.append('DISTANCE_REVIEW')
        p={k:float(v) if np.isfinite(v) else None
           for k,v in zip(('Ni_pct','Co_pct'),y)}
        return dict(condition=dict(zip(CONTROLS,map(float,x[8:]))),
                    raw_prediction=p,prediction=None if flags else p.copy(),
                    usable=not flags,warnings=flags,
                    distance=float(distance) if np.isfinite(distance) else None)

    def predict(self, values):
        x=self.input_vector(values);y,d=self.calculate(x[None,:])
        return self.row(x,y[0],d[0])


def main(argv=None):
    """Predict one complete 11-feature JSON input without training."""
    import argparse
    parser=argparse.ArgumentParser(description='학습 완료 모델로 Ni/Co 회수율을 예측합니다.')
    root=Path(__file__).resolve().parents[1]
    parser.add_argument('--input',type=Path,default=root/'data/examples/example_input.json')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    result=Engine().predict(json.loads(args.input.read_text(encoding='utf-8')))
    content=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(content+'\n',encoding='utf-8')
    print(content)
    return result


if __name__=='__main__':
    main()
