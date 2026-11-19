import type { AnalysisResult, AnalyzeRequest, ProcessConditions } from '../../api/types'

export interface AnalysisSnapshot { result: AnalysisResult; input: AnalyzeRequest }
export const initialProcessInput = {
  name: '', ni_content_pct: '', co_content_pct: '',
  li_content_pct: '', mn_content_pct: '', cu_content_pct: '', fe_content_pct: '', al_content_pct: '',
  feed_amount_kg: '',
  sulfuric_acid_l: '', leaching_temperature_c: '', leaching_time_hr: '',
}
export type ProcessInput = typeof initialProcessInput
export type NumericInputField = Exclude<keyof ProcessInput, 'name'>
export type FieldErrors = Partial<Record<NumericInputField, string>>

// Live limits match the A model validation in a_http.py.
export const materialFields = [
  { key: 'ni_content_pct', label: '니켈 함량 (%)', unit: '%', min: 8, max: 30 },
  { key: 'co_content_pct', label: '코발트 함량 (%)', unit: '%', min: 2, max: 15 },
  { key: 'li_content_pct', label: '리튬 함량 (%)', unit: '%', min: 2, max: 6 },
  { key: 'mn_content_pct', label: '망간 함량 (%)', unit: '%', min: 5, max: 16 },
  { key: 'cu_content_pct', label: '구리 불순물 (%)', unit: '%', min: 0.3, max: 6 },
  { key: 'fe_content_pct', label: '철 불순물 (%)', unit: '%', min: 0.2, max: 6 },
  { key: 'al_content_pct', label: '알루미늄 불순물 (%)', unit: '%', min: 0.5, max: 7 },
  { key: 'feed_amount_kg', label: '원료 투입량 (kg)', unit: 'kg', min: 80, max: 200 },
] as const

export function formatDisplayNumber(value: number | null | undefined) {
  return value == null ? '—' : Number(value.toFixed(2))
}
export function toAnalyzeRequest(values: ProcessInput): AnalyzeRequest {
  const number = (value: string) => value.trim() === '' ? null : Number(value)
  return {
    material: {
      name: values.name.trim() || null,
      ni_content_pct: number(values.ni_content_pct),
      co_content_pct: number(values.co_content_pct),
      li_content_pct: number(values.li_content_pct),
      mn_content_pct: number(values.mn_content_pct),
      cu_content_pct: number(values.cu_content_pct),
      fe_content_pct: number(values.fe_content_pct),
      al_content_pct: number(values.al_content_pct),
    },
    current_process: { feed_amount_kg: number(values.feed_amount_kg), sulfuric_acid_l: number(values.sulfuric_acid_l),
      leaching_temperature_c: number(values.leaching_temperature_c), leaching_time_hr: number(values.leaching_time_hr) },
  }
}
export function toRecommendationRequest(input: AnalyzeRequest): AnalyzeRequest {
  return {
    material: input.material,
    current_process: {
      feed_amount_kg: input.current_process.feed_amount_kg,
      sulfuric_acid_l: null,
      leaching_temperature_c: null,
      leaching_time_hr: null,
    },
  }
}
export function processConditionsFromRequest(input: AnalyzeRequest): ProcessConditions | null {
  const { sulfuric_acid_l, leaching_temperature_c, leaching_time_hr } = input.current_process
  if (sulfuric_acid_l === null || leaching_temperature_c === null || leaching_time_hr === null ||
      ![sulfuric_acid_l, leaching_temperature_c, leaching_time_hr].every(Number.isFinite) ||
      sulfuric_acid_l < 0 || leaching_time_hr < 0) return null
  return { sulfuric_acid_l, leaching_temperature_c, leaching_time_hr }
}

export const conditionFields = [
  { key: 'sulfuric_acid_l', label: '황산 투입량', unit: 'L', min: 400, max: 1500 },
  { key: 'leaching_temperature_c', label: '침출 온도', unit: '°C', min: 40, max: 95 },
  { key: 'leaching_time_hr', label: '침출 시간', unit: '시간', min: 1, max: 8 },
] as const

const numericFields = [...materialFields, ...conditionFields]

export function numericFieldFromPath(path: string): NumericInputField | undefined {
  return numericFields.find(({ key }) =>
    path === `material.${key}` || path === `current_process.${key}` || path === `process_conditions.${key}`)?.key
}

export function numericFieldErrors(values: ProcessInput, live: boolean): FieldErrors {
  const errors: FieldErrors = {}
  for (const { key, unit, min, max } of numericFields) {
    const raw = values[key].trim()
    if (raw === '') continue
    const value = Number(raw)
    const lower = live ? min : key === 'leaching_temperature_c' ? -Infinity : 0
    const upper = live ? max : unit === '%' ? 100 : Infinity
    const suffix = unit === '%' ? '%' : ` ${unit}`
    if (!Number.isFinite(value)) {
      errors[key] = '유효한 숫자를 입력해 주세요.'
    } else if (value < lower || value > upper) {
      errors[key] = Number.isFinite(upper)
        ? `${lower}~${upper}${suffix} 범위로 입력해 주세요.`
        : `${lower}${suffix} 이상 입력해 주세요.`
    }
  }
  return errors
}
