import { afterEach, describe, expect, it, vi } from 'vitest'
import { readWorkHistory, saveWorkHistory, WORK_HISTORY_KEY, type WorkRecord } from './workHistoryStore'
import { initialProcessInput, toAnalyzeRequest } from './processInput'

const record: WorkRecord = {
  commandId: 'command-1', appliedAt: '2026-11-17T00:00:00Z', analysisRequestId: 'analysis-1', source: 'mock',
  input: toAnalyzeRequest({ ...initialProcessInput, li_content_pct: '0', sulfuric_acid_l: '1050', leaching_temperature_c: '62', leaching_time_hr: '5.5' }),
  prediction: { ni_recovery_pct: 89.2, co_recovery_pct: 82.1 },
}
afterEach(() => { vi.restoreAllMocks(); localStorage.clear() })

describe('browser work history storage', () => {
  it('retains missing values and actual zero values when reloading', () => {
    saveWorkHistory([record])
    const loaded = readWorkHistory()
    expect(loaded.warning).toBeNull()
    expect(loaded.items).toEqual([record])
    expect(loaded.items[0].input.material.li_content_pct).toBe(0)
    expect(loaded.items[0].input.material.fe_content_pct).toBeNull()
  })
  it.each(['{broken', JSON.stringify({ version: 1, items: [{ ...record, prediction: null }] })])('does not crash or overwrite unreadable history', (raw) => {
    localStorage.setItem(WORK_HISTORY_KEY, raw)
    const loaded = readWorkHistory()
    expect(loaded.items).toEqual([])
    expect(loaded.warning).toContain('작업 기록을 읽을 수 없습니다')
    expect(localStorage.getItem(WORK_HISTORY_KEY)).toBe(raw)
  })
  it('handles browser storage access being blocked', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new DOMException('Blocked', 'SecurityError') })
    expect(readWorkHistory().warning).not.toBeNull()
  })
})
