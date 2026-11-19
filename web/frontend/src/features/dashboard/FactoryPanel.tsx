import type { AnalysisResult } from '../../api/types'
import { InputIssue } from './InputIssue'
import { conditionFields, formatDisplayNumber, type FieldErrors, type ProcessInput } from './processInput'

interface Props {
  recommendation: AnalysisResult | null
  onUseRecommendation: () => void
  recommendationDisabled: boolean
  canApply: boolean
  onApply: () => void
  applyBlockedReason: string | null
  applying: boolean
  values: ProcessInput
  fieldErrors: FieldErrors
  onChange: (key: keyof ProcessInput, value: string) => void
  onAnalyze: () => void
  analyzing: boolean
  busy: boolean
  canPredict: boolean
  prediction: AnalysisResult['current_prediction'] | null
}
export function FactoryPanel({
  recommendation, onUseRecommendation, recommendationDisabled,
  canApply, onApply, applyBlockedReason, applying,
  values, fieldErrors, onChange, onAnalyze, analyzing, busy, canPredict, prediction,
}: Props) {
  return <section className="factory-panel process-workspace" aria-labelledby="process-condition-heading">
    <h3 id="process-condition-heading" tabIndex={-1}>공정 조건 설정</h3>
    <form id="process-conditions-form" className="process-editor" onSubmit={(event) => { event.preventDefault(); onAnalyze() }}>
      <div className="selection-table-wrap">
        <table className="selection-table" aria-label="추천 공정 조건">
          <thead><tr><th scope="col">공정 항목</th><th scope="col">AI 추천값</th><th scope="col">적용할 조건 · 수정 가능</th></tr></thead>
          <tbody>{conditionFields.map(({ key, label, unit }) => {
            const id = `draft-${key}`
            const issue = fieldErrors[key]
            return <tr key={key}>
              <th scope="row"><label htmlFor={id}>{label} ({unit})</label></th>
              <td className="selection-recommended"><div className="recommended-value"><strong>{recommendation?.recommendation?.process_conditions[key] ?? '—'}</strong><span>{unit}</span></div></td>
              <td><div className="selection-input">
                <div className="numeric-field">
                  <input id={id} type="number" step="any" value={values[key]} disabled={applying}
                    aria-invalid={issue ? true : undefined} aria-describedby={issue ? `${id}-error` : undefined}
                    onChange={(event) => onChange(key, event.target.value)} />
                  {issue && <InputIssue id={`${id}-error`} label={`${label} (${unit})`} message={issue} />}
                </div>
                <span aria-hidden="true">{unit}</span>
              </div></td>
            </tr>
          })}</tbody>
        </table>
      </div>
    </form>
    <div className="selection-forecasts">
    <div className="selection-row-label"><strong>예상 회수율</strong></div>
    <div className="forecast-card recommended-forecast" role="group" aria-label="추천 조건 예상 회수율">
      <p className="forecast-label">추천 조건 예상 회수율</p>
      <div className="forecast-values">
        <div role="group" aria-label="니켈 추천 회수율"><span>Ni</span><strong>{formatDisplayNumber(recommendation?.recommendation?.expected_recovery.ni_recovery_pct)}%</strong></div>
        <div role="group" aria-label="코발트 추천 회수율"><span>Co</span><strong>{formatDisplayNumber(recommendation?.recommendation?.expected_recovery.co_recovery_pct)}%</strong></div>
      </div>
    </div>
    <div className="forecast-card confirmed-forecast" role="group" aria-label="입력 조건 예상 회수율">
      <p className="forecast-label">입력 조건 예상 회수율</p>
      <div className="forecast-values">
        <div><span>Ni</span><strong>{formatDisplayNumber(prediction?.ni_recovery_pct)}%</strong></div>
        <div><span>Co</span><strong>{formatDisplayNumber(prediction?.co_recovery_pct)}%</strong></div>
      </div>
    </div>
    </div>
      <div className="selection-actions" role="group" aria-label="공정 조건 작업">
        <div className="selection-row-label"><strong>조건 선택</strong>
        </div>
        <div className="selection-action recommendation-action">
          <button className="secondary-button" type="button" disabled={!recommendation?.recommendation || recommendationDisabled} onClick={onUseRecommendation}>추천값 적용하기</button>
        </div>
        <div className="selection-action prediction-action">
          <button className="secondary-button" type="submit" form="process-conditions-form" disabled={busy || applying || !canPredict}>{analyzing ? '예측 중...' : '회수율 예측'}</button>
        </div>
      </div>
    {recommendation?.status && !recommendation.recommendation && !recommendationDisabled &&
      <aside className="a-recommendation-notice" aria-label="추천 결과 안내">
        모델이 지원하는 범위에서 추천할 조건을 찾지 못했습니다.
      </aside>}
    <div className="factory-actions">
      <p className="notice apply-hint" id="apply-blocked-reason" aria-live="polite">{applyBlockedReason ?? ''}</p>
      <button className="primary-button" type="button" disabled={!canApply || applying} onClick={onApply} aria-describedby="apply-blocked-reason">{applying ? '명령 전송 중...' : '가상 공장에 적용'}</button>
    </div>
  </section>
}
