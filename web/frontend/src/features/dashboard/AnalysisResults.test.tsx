import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { AnalysisResult, AnalyzeRequest } from '../../api/types'
import { AnalysisResults } from './AnalysisResults'

const input: AnalyzeRequest = {
  material: {
    name: '원료 1', ni_content_pct: 12, co_content_pct: 6,
    li_content_pct: null, mn_content_pct: null, cu_content_pct: null,
    fe_content_pct: null, al_content_pct: null,
  },
  current_process: { feed_amount_kg: 1000, sulfuric_acid_l: 1100,
    leaching_temperature_c: 58, leaching_time_hr: 6 },
}
const result: AnalysisResult = {
  schema_version: 'draft-1', source: 'mock', request_id: 'analysis-123',
  generated_at: '2026-11-03T00:00:00Z',
  current_prediction: { ni_recovery_pct: 85.65, co_recovery_pct: 78.45 },
  recommendation: {
    process_conditions: { sulfuric_acid_l: 1050, leaching_temperature_c: 62, leaching_time_hr: 5.5 },
    expected_recovery: { ni_recovery_pct: 89.2, co_recovery_pct: 77.45 },
  },
}

describe('analysis comparison', () => {
  it('shows recovery direction, relative process changes and recommendation material basis', () => {
    render(<AnalysisResults result={result} input={input} recommendationInput={{ ...input,
      material: { ...input.material, name: '추천 원료', li_content_pct: 0 },
    }} />)
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByText('추천 원료')).toBeVisible()
    expect(within(dialog).getByText('투입량 1000 kg')).toBeVisible()
    expect(within(screen.getByRole('region', { name: '추천에 사용한 원료' })).getByText('0%')).toBeVisible()
    expect(screen.getByRole('group', { name: '니켈 회수율 변화' })).toHaveTextContent('↑ 증가')
    expect(screen.getByRole('group', { name: '코발트 회수율 변화' })).toHaveTextContent('↓ 감소')
    expect(screen.getByRole('row', { name: /황산 투입량/ })).toHaveTextContent('-4.55 %')
    expect(screen.getByRole('row', { name: /침출 온도/ })).toHaveTextContent('—')
  })
  it('does not invent a percentage from zero inputs or a missing prediction', () => {
    render(<AnalysisResults result={result} input={{ ...input,
      current_process: { ...input.current_process, sulfuric_acid_l: 0 },
    }} currentPrediction={null} />)
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    const acid = screen.getByRole('row', { name: /황산 투입량/ })
    expect(within(acid).getByText('0 L')).toBeVisible()
    expect(within(acid).getByText('—')).toBeVisible()
    expect(screen.getByRole('group', { name: '니켈 회수율 변화' })).toHaveTextContent('비교 대기')
    expect(screen.queryByRole('meter', { name: '니켈 현재 조건 예상 회수율' })).not.toBeInTheDocument()
  })
  it('closes the modal, unlocks scrolling and returns focus to the opener', () => {
    render(<AnalysisResults result={result} input={input} />)
    const opener = screen.getByRole('button', { name: '상세 비교 보기' })
    fireEvent.click(opener)
    expect(screen.getByRole('dialog', { name: '공정 조건 상세 비교' })).toBeVisible()
    expect(document.body.style.overflow).toBe('hidden')
    expect(screen.getByRole('button', { name: '닫기' })).toHaveFocus()
    fireEvent.click(screen.getByRole('button', { name: '닫기' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(document.body.style.overflow).not.toBe('hidden')
    expect(opener).toHaveFocus()
    fireEvent.click(opener)
    fireEvent(screen.getByRole('dialog'), new Event('cancel', { bubbles: true, cancelable: true }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
  it('shows absolute recommended values prominently and keeps comparison collapsed', () => {
    render(<AnalysisResults result={result} input={input} />)
    expect(screen.getByText('다음 공정 조건을 추천합니다.')).toBeVisible()
    const values = screen.getByLabelText('추천 공정 조건')
    expect(within(values).getByText('1050')).toBeVisible()
    expect(within(values).getByText('62')).toBeVisible()
    expect(within(values).getByText('5.5')).toBeVisible()
    expect(screen.queryByRole('table', { name: '공정 조건 비교' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    expect(screen.getByRole('table', { name: '공정 조건 비교' })).toBeVisible()
  })
  it('compares conditions using signed differences in each field unit', () => {
    render(<AnalysisResults result={result} input={input} />)
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    const acid = screen.getByRole('row', { name: /황산 투입량/ })
    expect(within(acid).getByText('1100 L')).toBeInTheDocument()
    expect(within(acid).getByText('1050 L')).toBeInTheDocument()
    expect(within(acid).getByText('-50 L')).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /침출 온도/ })).toHaveTextContent('+4 °C')
    expect(screen.getByRole('row', { name: /침출 시간/ })).toHaveTextContent('-0.5 시간')
  })

  it('shows recovery changes in percentage points without floating-point noise', () => {
    render(<AnalysisResults result={result} input={input} />)
    expect(screen.queryByRole('group', { name: '니켈 회수율 변화' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    expect(screen.getByRole('group', { name: '니켈 회수율 변화' })).toHaveTextContent('+3.55 %p')
    expect(screen.getByRole('group', { name: '코발트 회수율 변화' })).toHaveTextContent('-1 %p')
  })

  it('keeps missing values incomparable and treats zero as an actual input', () => {
    render(<AnalysisResults result={result} input={{ ...input, current_process: {
      ...input.current_process, sulfuric_acid_l: null, leaching_temperature_c: 0, leaching_time_hr: 5.5,
    } }} />)
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    const acid = screen.getByRole('row', { name: /황산 투입량/ })
    expect(within(acid).getByText('미입력')).toBeInTheDocument()
    expect(within(acid).getByText('비교 불가')).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /침출 온도/ })).toHaveTextContent('+62 °C')
    expect(screen.getByRole('row', { name: /침출 시간/ })).toHaveTextContent('변화 없음')
  })

  it('shows current and recommended recovery in a common 0 to 100 graph', () => {
    render(<AnalysisResults result={result} input={input} />)
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    expect(screen.getByRole('meter', { name: '니켈 현재 조건 예상 회수율' })).toHaveAttribute('value', '85.65')
    expect(screen.getByRole('meter', { name: '니켈 추천 조건 예상 회수율' })).toHaveAttribute('value', '89.2')
    expect(screen.getByRole('meter', { name: '코발트 추천 조건 예상 회수율' })).toHaveAttribute('max', '100')
  })

  it('limits displayed comparison values to two decimal places while retaining precise graph values', () => {
    const recovery = 84.92398587306
    render(<AnalysisResults result={{ ...result, current_prediction: { ni_recovery_pct: recovery, co_recovery_pct: 78.45 } }}
      input={{ ...input, material: { ...input.material, ni_content_pct: 12.1756 },
        current_process: { ...input.current_process, feed_amount_kg: 159.12345, sulfuric_acid_l: 1118.12345 } }} />)
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    expect(screen.getByRole('group', { name: '니켈 회수율 변화' })).toHaveTextContent('84.92%')
    const meter = screen.getByRole('meter', { name: '니켈 현재 조건 예상 회수율' })
    expect(meter).toHaveTextContent('84.92%')
    expect(meter).toHaveAttribute('value', String(recovery))
    expect(screen.getByRole('row', { name: /황산 투입량/ })).toHaveTextContent('1118.12 L')
    const basis = within(screen.getByRole('region', { name: '추천에 사용한 원료' }))
    expect(basis.getByText('투입량 159.12 kg')).toBeVisible()
    expect(basis.getByText('12.18%')).toBeVisible()
  })

  it('reserves comparison and graph slots without inventing values before analysis', () => {
    render(<AnalysisResults result={null} input={null} />)
    expect(screen.getByRole('button', { name: '추천 조건 사용' })).toBeDisabled()
    expect(screen.getByText('원료 조건을 입력하고 추천을 받아보세요.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    expect(screen.getByRole('table', { name: '공정 조건 비교' })).toBeInTheDocument()
    expect(screen.getByRole('figure', { name: '예상 회수율 비교 그래프' })).toBeInTheDocument()
    expect(screen.queryAllByRole('meter')).toHaveLength(0)
  })

  it('keeps the grade hidden in the simplified UI even if A returns it', () => {
    render(<AnalysisResults result={{ ...result, material_grade: 'B' }} input={input} />)
    expect(screen.queryByText(/원료 등급/)).not.toBeInTheDocument()
  })
})
