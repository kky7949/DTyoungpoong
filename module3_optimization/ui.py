"""Optional interactive notebook panel using the same modular prediction engine."""
from module3_optimization.optimizer import Engine,make_axis
from module2_prediction.inference import FEATURES,CONTROLS,LIMITS,APP_VERSION,MODEL_VERSION
from module2_prediction.validation import numeric
import numpy as np


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
