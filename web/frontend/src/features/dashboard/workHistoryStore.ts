import type { AdapterMode, AnalyzeRequest, RecoveryPrediction } from '../../api/types'

export const WORK_HISTORY_KEY = 'youngpoong.hmi.work-history.v1'
export interface WorkRecord {
  commandId: string
  appliedAt: string
  analysisRequestId: string
  source: AdapterMode
  input: AnalyzeRequest
  prediction: RecoveryPrediction
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
function nullableNumber(value: unknown) {
  return value === null || typeof value === 'number' && Number.isFinite(value)
}
function validRecord(value: unknown): value is WorkRecord {
  if (!object(value) || !object(value.input) || !object(value.input.material) ||
    !object(value.input.current_process) || !object(value.prediction)) return false
  const material = value.input.material
  const process = value.input.current_process
  const prediction = value.prediction
  return typeof value.commandId === 'string' && value.commandId.length > 0 &&
    typeof value.analysisRequestId === 'string' && value.analysisRequestId.length > 0 &&
    typeof value.appliedAt === 'string' && Number.isFinite(Date.parse(value.appliedAt)) &&
    (value.source === 'mock' || value.source === 'live') &&
    (material.name === null || typeof material.name === 'string') &&
    ['ni_content_pct', 'co_content_pct', 'li_content_pct', 'mn_content_pct', 'cu_content_pct', 'fe_content_pct', 'al_content_pct'].every((key) => nullableNumber(material[key])) &&
    nullableNumber(process.feed_amount_kg) &&
    ['sulfuric_acid_l', 'leaching_temperature_c', 'leaching_time_hr'].every((key) => typeof process[key] === 'number' && Number.isFinite(process[key])) &&
    ['ni_recovery_pct', 'co_recovery_pct'].every((key) => typeof prediction[key] === 'number' && Number.isFinite(prediction[key]) && prediction[key] >= 0 && prediction[key] <= 100)
}

export function readWorkHistory(): { items: WorkRecord[]; warning: string | null } {
  try {
    const raw = localStorage.getItem(WORK_HISTORY_KEY)
    if (raw === null) return { items: [], warning: null }
    const data: unknown = JSON.parse(raw)
    if (!object(data) || data.version !== 1 || !Array.isArray(data.items) || !data.items.every(validRecord)) throw new Error('Invalid history')
    return { items: data.items, warning: null }
  } catch {
    return { items: [], warning: '브라우저의 작업 기록을 읽을 수 없습니다. 브라우저 저장 설정을 확인해 주세요.' }
  }
}

export function saveWorkHistory(items: WorkRecord[]) {
  localStorage.setItem(WORK_HISTORY_KEY, JSON.stringify({ version: 1, items }))
}
