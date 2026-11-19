import type { AnalysisResult, AnalyzeRequest, ProcessConditions } from '../../api/types'
import { RecoveryChart } from './RecoveryChart'
import { conditionFields, formatDisplayNumber } from './processInput'

const materialFields = [
  ['ni_content_pct', '니켈 Ni'], ['co_content_pct', '코발트 Co'],
  ['li_content_pct', '리튬 Li'], ['mn_content_pct', '망간 Mn'],
  ['cu_content_pct', '구리 Cu'], ['fe_content_pct', '철 Fe'], ['al_content_pct', '알루미늄 Al'],
] as const

function differenceText(current: number | null, recommended: number, unit: string): string {
  if (current === null) return '비교 불가'
  const difference = recommended - current
  if (difference === 0) return '변화 없음'
  const rounded = Number(difference.toFixed(2))
  if (rounded === 0) return `${difference > 0 ? '+' : '-'}0.01 ${unit} 미만`
  return `${rounded > 0 ? '+' : ''}${rounded} ${unit}`
}

// Temperature has no meaningful relative percentage on the Celsius scale.
function relativeChange(current: number | null, recommended: number, key: keyof ProcessConditions) {
  if (current === null || current === 0 || key === 'leaching_temperature_c') return '—'
  return differenceText(0, (recommended - current) / current * 100, '%')
}

interface Props {
  result: AnalysisResult | null
  input: AnalyzeRequest | null
  basis: AnalyzeRequest | null
  currentPrediction: AnalysisResult['current_prediction'] | null
  stale?: boolean
}

export function ComparisonDetails({ result, input, basis, currentPrediction, stale }: Props) {
  return <>
    <div className="comparison-context">
      <div><span className="detail-kicker">분석 대상</span><strong>{basis?.material.name || '원료 정보 없음'}</strong></div>
      <p>{stale ? '입력 또는 추천 목표가 변경됐습니다.' : !result?.recommendation ? '아직 추천 결과가 없습니다.' : !currentPrediction ? '입력 조건의 회수율 예측 전입니다.' : '입력 조건과 추천 조건의 예상값을 비교합니다.'}</p>
    </div>
    <section className="detail-section" aria-labelledby="recovery-detail-heading">
      <h3 id="recovery-detail-heading">예상 회수율 비교</h3>
      <div className="recovery-summary-grid">
        {([['ni_recovery_pct', '니켈', 'Ni'], ['co_recovery_pct', '코발트', 'Co']] as const).map(([key, label, symbol]) => {
          const current = currentPrediction?.[key] ?? null
          const recommended = result?.recommendation?.expected_recovery[key]
          const delta = recommended !== undefined && current !== null ? recommended - current : null
          return <div className="recovery-summary-card" key={key} role="group" aria-label={`${label} 회수율 변화`}>
            <div className="metric-title"><span className="metal-symbol">{symbol}</span><h4>{label} 회수율</h4></div>
            <div className="recovery-number"><span>추천 조건</span><strong>{formatDisplayNumber(recommended)}<small>%</small></strong></div>
            <div className="recovery-baseline"><span>입력 조건</span><b>{current === null ? '예측 전' : `${formatDisplayNumber(current)}%`}</b></div>
            <p className={`metric-delta ${delta === null ? 'pending' : delta > 0 ? 'increase' : delta < 0 ? 'decrease' : 'unchanged'}`}>
              <span>{delta === null ? '비교 대기' : delta > 0 ? '↑ 증가' : delta < 0 ? '↓ 감소' : '동일'}</span>
              <strong>{recommended === undefined ? '—' : current === null ? '입력 조건 예측 필요' : differenceText(current, recommended, '%p')}</strong>
            </p>
          </div>
        })}
      </div>
      <RecoveryChart result={result} currentPrediction={currentPrediction} />
    </section>
    <section className="detail-section" aria-labelledby="condition-detail-heading">
      <div className="detail-section-heading"><h3 id="condition-detail-heading">공정 설정값 비교</h3><span>변화량 = 추천 − 입력</span></div>
      <div className="comparison-scroll" role="region" aria-label="공정 조건 비교" tabIndex={0}>
        <table className="comparison-table" aria-label="공정 조건 비교">
          <caption className="sr-only">공정 조건 비교</caption>
          <thead><tr><th scope="col">항목</th><th scope="col">입력 조건</th><th scope="col">추천 조건</th><th scope="col">변화량</th><th scope="col">변화율</th></tr></thead>
          <tbody>{conditionFields.map(({ key, label, unit }) => {
            const current = result ? input?.current_process[key] ?? null : null
            const recommended = result?.recommendation?.process_conditions[key]
            return <tr key={key}>
              <th scope="row">{label}</th>
              <td>{!result ? '—' : current === null ? '미입력' : `${formatDisplayNumber(current)} ${unit}`}</td>
              <td className="recommended-cell">{recommended === undefined ? '—' : `${formatDisplayNumber(recommended)} ${unit}`}</td>
              <td>{recommended === undefined ? '—' : differenceText(current, recommended, unit)}</td>
              <td>{recommended === undefined ? '—' : relativeChange(current, recommended, key)}</td>
            </tr>
          })}</tbody>
        </table>
      </div>
      <p className="detail-footnote">변화율은 입력값 기준입니다. 입력값이 0이거나 온도인 경우 표시하지 않습니다.</p>
    </section>
    <section className="detail-section material-basis" aria-labelledby="material-basis-heading">
      <div className="detail-section-heading"><h3 id="material-basis-heading">추천에 사용한 원료</h3><span>투입량 {basis?.current_process.feed_amount_kg === null || !basis ? '미입력' : `${formatDisplayNumber(basis.current_process.feed_amount_kg)} kg`}</span></div>
      <dl className="material-metrics">{materialFields.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{basis?.material[key] === null || !basis ? '미입력' : `${formatDisplayNumber(basis.material[key])}%`}</dd></div>)}</dl>
    </section>
  </>
}
