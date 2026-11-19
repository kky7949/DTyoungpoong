import { InputIssue } from './InputIssue'
import { materialFields, type FieldErrors, type ProcessInput } from './processInput'
import type { RecommendationMode } from '../../api/types'

interface Props {
  locked: boolean
  values: ProcessInput
  fieldErrors: FieldErrors
  onChange: (key: keyof ProcessInput, value: string) => void
  onRecommend: () => void
  busy: boolean
  recommending: boolean
  recommendationMode: RecommendationMode
  recommendationModeEnabled: boolean
  onModeChange: (mode: RecommendationMode) => void
}
export function ProcessForm({ locked, values, fieldErrors, onChange, onRecommend, busy, recommending, recommendationMode, recommendationModeEnabled, onModeChange }: Props) {
  return <section className="panel process-form" aria-labelledby="material-heading">
    <div className="panel-heading"><div><p className="eyebrow">RAW MATERIAL</p><h2 id="material-heading">원료 조건</h2></div></div>
    <label>원료 이름<input id="material-name" value={values.name} disabled={locked} onChange={(event) => onChange('name', event.target.value)} /></label>
    <div className="field-grid">
      {materialFields.map(({ key, label, min, max }) => {
        const id = `material-${key}`
        const range = `${min}~${max}`
        const issue = fieldErrors[key]
        return <div key={key} className="material-field">
          <label htmlFor={id}>{label}</label>
          <div className="numeric-field">
            <input id={id} type="number" step="any" value={values[key]} placeholder={range} disabled={locked}
              aria-invalid={issue ? true : undefined} aria-describedby={issue ? `${id}-error` : `${id}-range`}
              onChange={(event) => onChange(key, event.target.value)} />
            {issue && <InputIssue id={`${id}-error`} label={label} message={issue} />}
            <span className="sr-only" id={`${id}-range`}>{range}</span>
          </div>
        </div>
      })}
    </div>
    <label className="recommendation-goal">
      <span id="recommendation-mode-label">추천 목표</span>
      <select aria-labelledby="recommendation-mode-label" aria-describedby={recommendationModeEnabled ? 'live-material-requirements' : undefined}
        value={recommendationMode} disabled={!recommendationModeEnabled || locked || busy}
        onChange={(event) => onModeChange(event.target.value as RecommendationMode)}>
        <option value="joint">동시 회수율 최대</option>
        <option value="ni">니켈 회수율 최대</option>
        <option value="co">코발트 회수율 최대</option>
      </select>
      <small id="live-material-requirements" style={{ visibility: recommendationModeEnabled ? 'visible' : 'hidden' }}>
        성분 7개와 투입량을 모두 입력해 주세요.
      </small>
    </label>
    <button className="primary-button recommend-button" type="button" onClick={onRecommend} disabled={locked || busy}>{recommending ? '추천 중...' : '최적 공정 추천'}</button>
  </section>
}
