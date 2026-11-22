# 영풍 과제 제출용 1.0 — 원본 업로드/재학습/이전 셀 불필요
# 모델: 기존 curve17의 학습 완료 수치. 외부 공정 자료 사용 안 함.
import base64, hashlib, lzma, math
from decimal import Decimal
from itertools import product
from collections.abc import Mapping
try:
    import numpy as np
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable,'-m','pip','install','-q','numpy'])
    import numpy as np

APP_VERSION = 'YP-course-final-1.0'
MODEL_VERSION = 'YP-curve17-dev357-v2'
FEATURES = ('Ni_함량_pct','Co_함량_pct','Li_함량_pct','Mn_함량_pct',
            'Cu_불순물_pct','Fe_불순물_pct','Al_불순물_pct',
            '원료투입량_kg','황산투입량_L','침출온도_C','침출시간_hr')
CONTROLS = FEATURES[8:]
LIMITS = np.array([(8,30),(2,15),(2,6),(5,16),(.3,6),(.2,6),
                   (.5,7),(80,200),(400,1500),(40,95),(1,8)],float)
# 모델 계수·표준화 통계·거리검사 참조값. 생략하거나 수정하지 마세요.
PAYLOAD = '''
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
'''
PAYLOAD_SHA = 'e9fa78c1c986780654b7bbebad021e747a0ad2031649d179c82715996b8838e5'


def numeric(value, name):
    if value is None or isinstance(value,(bool,np.bool_)) or not isinstance(
        value,(str,int,float,np.integer,np.floating)):
        raise ValueError(f'{name}: 숫자만 입력하세요.')
    try:
        value=float(value)
    except (ValueError,TypeError,OverflowError) as exc:
        raise ValueError(f'{name}: 숫자만 입력하세요.') from exc
    if not math.isfinite(value):
        raise ValueError(f'{name}: NaN·무한대는 허용하지 않습니다.')
    return value


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


class Engine:
    def __init__(self):
        packed=base64.b64decode(''.join(PAYLOAD.split()),validate=True)
        if hashlib.sha256(packed).hexdigest()!=PAYLOAD_SHA:
            raise ValueError('모델 문자열이 잘렸습니다. 코드를 전체 복사하세요.')
        raw=lzma.decompress(packed)
        if len(raw)!=4338: raise ValueError('모델 수치 길이 오류')
        v=np.frombuffer(raw,dtype='<f8',count=127)
        self.parameters=v[:104].reshape(2,52)
        self.dm=v[104:115]; self.ds=v[115:126]; self.threshold=float(v[126])
        factors=np.array([100]*7+[10,1,10,100])
        self.points=np.frombuffer(raw,dtype='<i2',offset=1016).reshape(11,151).T/factors
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
        a,t,h=x[:,8],x[:,9],x[:,10]
        z=np.column_stack((x,a*a,t*t,h*h,a*t,a*h,t*h))
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


def launch():
    import html
    import ipywidgets as w
    from IPython.display import display
    try:
        from google.colab import output
        output.enable_custom_widget_manager()
    except ImportError:
        pass
    engine=Engine(); rng=np.random.default_rng();state={'last':None,'error':None}
    def text(label, value='', placeholder=''):
        return w.Text(description=label,value=value,placeholder=placeholder,
            style={'description_width':'165px'},layout=w.Layout(width='350px'))
    labels=('Ni 함량(wt%)','Co 함량(wt%)','Li 함량(wt%)','Mn 함량(wt%)',
            'Cu 불순물(wt%)','Fe 불순물(wt%)','Al 불순물(wt%)',
            '원료투입량(kg)','황산투입량(L)','침출온도(°C)','침출시간(hr)')
    fields={k:text(label,placeholder=f'{lo:g}~{hi:g}')
            for k,label,(lo,hi) in zip(FEATURES,labels,LIMITS)}
    mode=w.Dropdown(options=[('세 모드 비교','all'),('현재 회수율만','predict'),
        ('두 최소치 + 동시 최대화','joint'),('Ni 최대화 / Co 하한 없음','ni'),
        ('Co 최대화 / Ni 하한 없음','co')],value='all',description='실행 모드',layout=w.Layout(width='450px'))
    ni=text('동시형 Ni 최소(%)','95');co=text('동시형 Co 최소(%)','90')
    rule=w.Dropdown(options=[('100%까지 제곱거리 최소 · 동일 가중','distance'),
        ('둘 중 낮은 회수율 최대화','maximin')],value='distance',description='공동 기준',layout=w.Layout(width='490px'))
    goal_panel=w.VBox([ni,co,rule]);axes={};grid_rows=[]
    for k,limits,step in zip(CONTROLS,LIMITS[8:],(50,5,.5)):
        boxes=[w.Text(value=str(v),layout=w.Layout(width='85px')) for v in (*limits,step)]
        axes[k]=boxes;grid_rows.append(w.HBox([w.Label(k,layout=w.Layout(width='170px')),*boxes]))
    grid_panel=w.VBox([w.HTML('<b>공정 탐색: 하한 / 상한 / 간격</b>'),*grid_rows])
    show_top=w.Checkbox(value=True,description='대표 포함 상위 3개 후보 표시')
    rand=w.Button(description='랜덤 입력 채우기');run=w.Button(description='예측·추천 실행',button_style='primary')
    status=w.HTML();out=w.HTML();busy={'value':False}
    names={'joint':'동시 최대화','ni':'Ni 우선 · Co 하한 없음','co':'Co 우선 · Ni 하한 없음'}
    states={'RECOMMENDED_ON_PREDICTION':'점예측 기준 선정',
        'TARGET_NOT_FOUND_IN_GRID':'동시 목표 미발견',
        'TARGET_FOUND_BUT_UNSUPPORTED':'목표 예측은 있으나 거리기준으로 제외',
        'NO_SUPPORTED_CANDIDATE':'거리기준 안의 유효 후보 없음',
        'NO_VALID_MODEL_OUTPUT':'출력 0~100% 검사 통과 후보 없음'}
    def esc(v):return html.escape(str(v))
    def fmt(v):return '—' if v is None else f'{float(v):.3f}'
    def table(heads,rows):
        return '<table><tr>'+''.join(f'<th style="padding:8px">{esc(h)}</th>' for h in heads)+'</tr>'+''.join(
            '<tr>'+''.join(f'<td style="padding:8px;border-top:1px solid #888">{esc(v)}</td>' for v in row)+'</tr>' for row in rows)+'</table>'
    def changed(_=None):
        if busy['value']:return
        state['last']=None;state['error']=None;out.value=''
        goal_panel.layout.display='' if mode.value in ('all','joint') else 'none'
        grid_panel.layout.display='none' if mode.value=='predict' else ''
        status.value=f'{APP_VERSION} | {MODEL_VERSION}<br>입력 후 실행하세요. 산 최소화 없음.'
    def randomize(_):
        i=int(rng.integers(len(engine.points)));d=((engine.reference-engine.reference[i])**2).sum(1);d[i]=np.inf
        j=int(rng.choice(np.argsort(d)[:5]));a=rng.uniform(.15,.85)
        values=a*engine.points[i]+(1-a)*engine.points[j]
        for (k,box),v,digits in zip(fields.items(),values,[3]*7+[1,1,1,2]):box.value=f'{v:.{digits}f}'
        status.value+=' 랜덤값은 합성 입력입니다. 목표·탐색 설정은 유지했습니다.'
    def output_row(label,item,status_text,baseline):
        if item is None:return [label,status_text,*['—']*7]
        p=item['prediction'];b=baseline['prediction'];c=item['condition']
        vals=[p[k] if p else None for k in ('Ni_pct','Co_pct')]
        delta=[p[k]-b[k] if p and b and label!='현재 입력' else None for k in ('Ni_pct','Co_pct')]
        return [label,status_text,*map(fmt,vals),*map(fmt,delta),*map(fmt,[c[k] for k in CONTROLS])]
    controls=[*fields.values(),mode,ni,co,rule,show_top,*[q for boxes in axes.values() for q in boxes]]
    def execute(_):
        busy['value']=True;state['last']=None;state['error']=None;out.value=''
        for q in [*controls,rand,run]:q.disabled=True
        status.value='계산 중입니다.'
        try:
            values={k:numeric(q.value,k) for k,q in fields.items()};base=engine.predict(values)
            parts=[];rows=[output_row('현재 입력',base,'예측값' if base['usable'] else '검토 보류',base)]
            if base['prediction']:
                p=base['prediction'];parts.append(f'<h3>예상 회수율: Ni {p["Ni_pct"]:.3f}% / Co {p["Co_pct"]:.3f}%</h3>')
            else:parts.append('<p>현재 입력 경고: '+esc(base['warnings'])+' / 진단용 원시 예측: '+esc(base['raw_prediction'])+'</p>')
            result=None;details=[]
            if mode.value!='predict':
                grid={k:make_axis(*(q.value for q in boxes),LIMITS[8+i]) for i,(k,boxes) in enumerate(axes.items())}
                floors=(ni.value,co.value) if mode.value in ('all','joint') else (0,0)
                result=engine.compare(values,*floors,rule.value,grid)
                modes=list(names) if mode.value=='all' else [mode.value]
                for k in modes:
                    info=result['modes'][k];item=info['recommendation']
                    rows.append(output_row(names[k],item,states[info['status']],base))
                    alt=info['closest_alternative']
                    if alt is not None:
                        rows.append(output_row('동시 목표 미달 대안',alt,'추천 아님 · 최소치 미충족',base))
                    chosen=item or alt
                    if k=='joint' and chosen:
                        margin=chosen['margin_pp'];details.append(f'<p>동시형 최소치 대비 여유: Ni {margin["Ni"]:+.3f}%p / Co {margin["Co"]:+.3f}%p</p>')
                    details.append(f'<p>{names[k]}: 선정 가능 {info["eligible_count"]}개 / 거리 제외 전 충족 {info["raw_feasible"]}개 / 충족했으나 거리 제외 {info["unsupported_feasible"]}개</p>')
                    if show_top.value and info['top_candidates']:
                        entries=[];leader=info['top_candidates'][0]['prediction']
                        for rank,q in enumerate(info['top_candidates'],1):
                            p=q['prediction'];c=q['condition']
                            entries.append([rank,*map(fmt,[p['Ni_pct'],p['Co_pct'],p['Ni_pct']-leader['Ni_pct'],p['Co_pct']-leader['Co_pct'],*[c[t] for t in CONTROLS]])])
                        details.append('<h4>'+names[k]+' — 대표 포함 상위 후보</h4>'+table(
                            ['순위','Ni(%)','Co(%)','1위 대비 Ni(%p)','1위 대비 Co(%p)','황산(L)','온도(°C)','시간(hr)'],entries))
                parts.append(f'<p>후보 {result["candidate_count"]:,} / 유효 {result["valid_count"]:,} / 출력 제외 {result["output_rejected"]:,} / 거리 제외 {result["distance_rejected"]:,}</p>')
                if mode.value in ('all','joint') and result['modes']['joint']['index'] is None:
                    parts.append('<p>지원범위 내 개별 최대 예측(각각 다른 조건일 수 있음): '+esc(result['supported_max_pct'])+'</p>')
                if result['same_candidate_all'] and mode.value=='all':parts.append('<p><b>세 목적의 공통 최적 후보입니다. 서로 다른 결과를 강제하지 않습니다.</b></p>')
            parts.append(table(['구분','상태','Ni 예측(%)','Co 예측(%)','Ni 변화(%p)','Co 변화(%p)','황산(L)','온도(°C)','시간(hr)'],rows))
            parts.extend(details)
            parts.append('<p><b>해석:</b> 현재 모델·격자의 계산상 순위입니다. 상위 후보를 동등하거나 우월하다고 통계적으로 인증한 결과가 아닙니다. 목표 달성 확률·실제 공정 안전을 보장하지 않습니다. 거리 점수는 신뢰구간이 아닙니다.</p>')
            out.value=''.join(parts);state['last']={'inputs':values,'current':base,'result':result}
            status.value=f'<b>실행 완료</b> | {APP_VERSION} | {MODEL_VERSION}'
        except Exception as exc:
            state['error']=f'{type(exc).__name__}: {exc}';status.value='<b>입력·실행 오류</b>';out.value=esc(state['error'])
        finally:
            busy['value']=False
            for q in [*controls,rand,run]:q.disabled=False
    for q in controls:q.observe(changed,names='value')
    rand.on_click(randomize);run.on_click(execute);changed()
    panel=w.VBox([w.HTML('<h3>영풍 회수율 예측·추천 — 과제 제출용</h3><p>11개 입력 / 학습 완료 모델 / 원본 업로드 없음</p>'),
        w.Box(list(fields.values()),layout=w.Layout(display='flex',flex_flow='row wrap')),mode,goal_panel,grid_panel,
        show_top,w.HBox([rand,run]),status,out])
    display(panel)
    return dict(panel=panel,inputs=fields,mode=mode,ni=ni,co=co,rule=rule,axes=axes,
                random=rand,run=run,state=state,output=out,engine=engine)


if __name__=='__main__':
    import importlib.util, subprocess, sys
    if importlib.util.find_spec('ipywidgets') is None:
        subprocess.check_call([sys.executable,'-m','pip','install','-q','ipywidgets>=8,<9'])
    if 'YP_FINAL_APP' in globals():
        YP_FINAL_APP['run'].disabled=YP_FINAL_APP['random'].disabled=True
        YP_FINAL_APP['panel'].close()
    YP_FINAL_APP=launch()
