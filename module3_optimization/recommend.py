"""CLI, audit tables and response plot for the final grid recommendation policy."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from module2_prediction.inference import FEATURES,CONTROLS,LIMITS
from .optimizer import Engine,make_axis

ROOT=Path(__file__).resolve().parents[1]

def _write_table(path,rows):
    fields=['mode','result_type','rank','status','Ni_pct','Co_pct',*CONTROLS,
            'Ni_margin_pp','Co_margin_pp','distance']
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)

def run_recommendation(input_path=None,output_path=None,ni_min=95,co_min=90,
                       joint_rule='distance',steps=(50,5,.5)):
    input_path=Path(input_path) if input_path else ROOT/'data/examples/example_input.json'
    output_path=Path(output_path) if output_path else Path(__file__).parent/'results/recommendations.json'
    values=json.loads(input_path.read_text(encoding='utf-8'))
    engine=Engine()
    grid=dict(zip(CONTROLS,[make_axis(lo,hi,step,(lo,hi)) for (lo,hi),step in zip(LIMITS[8:],steps)]))
    result=engine.compare(values,ni_min,co_min,joint_rule,grid)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    rows=[]
    for mode,info in result['modes'].items():
        candidates=[('recommendation',rank,r) for rank,r in enumerate(info['top_candidates'],1)]
        if info['closest_alternative'] is not None:
            candidates.append(('alternative_not_recommendation',None,info['closest_alternative']))
        for kind,rank,row in candidates:
            margins=row['margin_pp'] or {}
            rows.append(dict(mode=mode,result_type=kind,rank=rank,status=info['status'],
                             **row['raw_prediction'],**row['condition'],
                             Ni_margin_pp=margins.get('Ni'),Co_margin_pp=margins.get('Co'),distance=row['distance']))
    table_path=output_path.with_name(output_path.stem+'_top_candidates.csv')
    _write_table(table_path,rows)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(13,3.8))
    base=engine.input_vector(values)
    labels=['Sulfuric acid (L)','Temperature (C)','Leaching time (h)']
    for j,ax in enumerate(axes,8):
        x=np.tile(base,(101,1));x[:,j]=np.linspace(*LIMITS[j],101)
        predictions,distances=engine.calculate(x)
        valid=np.isfinite(predictions).all(1)&(predictions>=0).all(1)&(predictions<=100).all(1)&(distances<=engine.threshold)
        for column,metal,color in [(0,'Ni','#1267A5'),(1,'Co','#C05B20')]:
            ax.plot(x[:,j],predictions[:,column],color=color,alpha=.25)
            ax.plot(x[:,j],np.where(valid,predictions[:,column],np.nan),label=metal,color=color,lw=2)
        ax.set_xlabel(labels[j-8]);ax.set_ylabel('Predicted recovery (%)');ax.grid(alpha=.2)
    axes[0].legend()
    fig.suptitle('One control at a time; other inputs fixed at supplied values. Faint = excluded conditions.',fontsize=10)
    fig.tight_layout()
    figure_path=output_path.with_name(output_path.stem+'_response.png')
    fig.savefig(figure_path,dpi=150);plt.close(fig)
    return {'result':result,'files':{'recommendations':str(output_path),
                                   'top_candidates':str(table_path),'response_plot':str(figure_path)}}

def main(argv=None):
    p=argparse.ArgumentParser(description='같은 예측표에서 목표 달성/Ni 우선/Co 우선 조건을 추천합니다.')
    p.add_argument('--input',type=Path,default=ROOT/'data/examples/example_input.json')
    p.add_argument('--output',type=Path,default=Path(__file__).parent/'results/recommendations.json')
    p.add_argument('--ni-min',type=float,default=95);p.add_argument('--co-min',type=float,default=90)
    p.add_argument('--joint-rule',choices=['distance','maximin'],default='distance')
    p.add_argument('--acid-step',type=float,default=50);p.add_argument('--temperature-step',type=float,default=5)
    p.add_argument('--time-step',type=float,default=.5)
    a=p.parse_args(argv)
    result=run_recommendation(a.input,a.output,a.ni_min,a.co_min,a.joint_rule,
                              (a.acid_step,a.temperature_step,a.time_step))
    r=result['result']
    print(json.dumps({'model_version':r['model_version'],'candidate_count':r['candidate_count'],
                      'valid_count':r['valid_count'],'modes':{k:v['status'] for k,v in r['modes'].items()},
                      'files':result['files']},ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
    main()
