import { useState, type FormEvent } from 'react'

import type { AnalyzeRequest } from '../../api/types'

interface Props {
  loading: boolean
  onSubmit: (payload: AnalyzeRequest) => void
}

type FieldName =
  | 'ni_content_pct'
  | 'co_content_pct'
  | 'feed_amount_kg'
  | 'sulfuric_acid_l'
  | 'leaching_temperature_c'
  | 'leaching_time_hr'

const initialValues: Record<FieldName, string> = {
  ni_content_pct: '12.17',
  co_content_pct: '2.41',
  feed_amount_kg: '1000',
  sulfuric_acid_l: '980',
  leaching_temperature_c: '58',
  leaching_time_hr: '5',
}

function nullableNumber(value: string): number | null {
  return value.trim() === '' ? null : Number(value)
}

export function ProcessForm({ loading, onSubmit }: Props) {
  const [grade, setGrade] = useState('혼합 원료 A')
  const [values, setValues] = useState(initialValues)

  function update(name: FieldName, value: string) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    onSubmit({
      material: {
        grade: grade.trim() || null,
        ni_content_pct: nullableNumber(values.ni_content_pct),
        co_content_pct: nullableNumber(values.co_content_pct),
      },
      current_process: {
        feed_amount_kg: nullableNumber(values.feed_amount_kg),
        sulfuric_acid_l: nullableNumber(values.sulfuric_acid_l),
        leaching_temperature_c: nullableNumber(values.leaching_temperature_c),
        leaching_time_hr: nullableNumber(values.leaching_time_hr),
      },
    })
  }

  const fields: Array<{ name: FieldName; label: string; step?: string }> = [
    { name: 'ni_content_pct', label: '니켈 함량 (%)', step: '0.01' },
    { name: 'co_content_pct', label: '코발트 함량 (%)', step: '0.01' },
    { name: 'feed_amount_kg', label: '원료 투입량 (kg)', step: '0.1' },
    { name: 'sulfuric_acid_l', label: '황산 투입량 (L)', step: '0.1' },
    { name: 'leaching_temperature_c', label: '침출 온도 (°C)', step: '0.1' },
    { name: 'leaching_time_hr', label: '침출 시간 (시간)', step: '0.1' },
  ]

  return (
    <form className="panel process-form" onSubmit={submit}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">PROCESS INPUT</p>
          <h2>현재 공정 조건</h2>
        </div>
        <span className="draft-badge">임시 명세</span>
      </div>
      <label>
        원료 등급
        <input value={grade} onChange={(event) => setGrade(event.target.value)} />
      </label>
      <div className="field-grid">
        {fields.map((field) => (
          <label key={field.name}>
            {field.label}
            <input
              type="number"
              step={field.step}
              value={values[field.name]}
              onChange={(event) => update(field.name, event.target.value)}
            />
          </label>
        ))}
      </div>
      <p className="helper-text">빈 값은 null로 전송하며, A 파트에서 결측값을 보정합니다.</p>
      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? '분석 중...' : '예측 및 최적화 실행'}
      </button>
    </form>
  )
}
