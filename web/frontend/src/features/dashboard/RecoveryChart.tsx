import type { AnalysisResult } from '../../api/types'
import { formatDisplayNumber } from './processInput'

interface Props {
  result: AnalysisResult | null
  currentPrediction?: AnalysisResult['current_prediction'] | null
}

export function RecoveryChart({ result, currentPrediction = result?.current_prediction ?? null }: Props) {
  return (
    <figure className="recovery-chart" aria-label="예상 회수율 비교 그래프">
      <figcaption>예상 회수율 <span className="chart-legend"><span className="legend-current">입력 조건</span><span className="legend-recommended">추천 조건</span></span></figcaption>
      <div className="chart-scale" aria-hidden="true"><span>0%</span><span>50%</span><span>100%</span></div>
      {([['ni_recovery_pct', '니켈', 'Ni'], ['co_recovery_pct', '코발트', 'Co']] as const).map(([key, label, symbol]) => (
        <div className="chart-metal" key={key}>
          <span className="metal-label">{symbol}</span>
          <div className="chart-pair">
            {(['current', 'recommended'] as const).map((kind) => {
              const value = kind === 'current' ? currentPrediction?.[key] ?? null : result?.recommendation?.expected_recovery[key] ?? null
              const percentage = value === null ? '—' : `${formatDisplayNumber(value)}%`
              const name = `${label} ${kind === 'current' ? '현재' : '추천'} 조건 예상 회수율`
              return <div className={`chart-bar ${kind}`} key={kind}>
                <span className="chart-bar-name">{kind === 'current' ? '입력' : '추천'}</span>
                {value === null ? <div className="chart-placeholder" /> :
                  <meter min={0} max={100} value={value} aria-label={name} aria-valuetext={percentage}>{percentage}</meter>}
                <span>{percentage}</span>
              </div>
            })}
          </div>
        </div>
      ))}
    </figure>
  )
}
