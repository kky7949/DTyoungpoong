import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { FactoryState } from '../../api/types'
import { UnityStatus } from './UnityStatus'

const running: FactoryState = {
  source: 'mock', state: 'running', command_id: 'command-123', progress_pct: 35,
  message: '침출 공정 실행 중', updated_at: '2026-11-17T10:00:00Z',
  connection_status: 'connected', last_seen_at: '2026-11-17T10:00:00Z',
}
describe('equipment operating panel', () => {
  it('separates connection, operation, progress and the reported message', () => {
    const progress = 35.128765
    render(<UnityStatus state={{ ...running, progress_pct: progress }} queued={false} unavailable={false} />)
    expect(screen.getByText('연결됨')).toBeVisible()
    expect(screen.getByText('실행 중 · 35.13%')).toBeVisible()
    expect(screen.getByRole('progressbar', { name: '공정 진행률' })).toHaveAttribute('value', String(progress))
    expect(screen.getByRole('status')).toHaveTextContent('침출 공정 실행 중')
    expect(screen.getByText('마지막 통신')).toBeVisible()
  })
  it('does not invent progress before an execution exists', () => {
    render(<UnityStatus state={{ ...running, state: 'idle', command_id: null, progress_pct: 0 }} queued={false} unavailable={false} />)
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    expect(screen.getByText('대기')).toBeVisible()
  })
  it.each(['disconnected', 'unavailable'] as const)('labels retained progress as historical when %s', (reason) => {
    render(<UnityStatus state={{ ...running, connection_status: reason === 'disconnected' ? 'disconnected' : 'connected' }} queued={false} unavailable={reason === 'unavailable'} />)
    expect(screen.getByText('마지막 확인 상태')).toBeVisible()
    expect(screen.getByRole('progressbar', { name: '마지막 확인 공정 진행률' })).toHaveAttribute('value', '35')
    expect(screen.queryByText('연결됨')).not.toBeInTheDocument()
    expect(screen.getByText('공정 상태와 진행률은 마지막 보고 기준입니다.')).toBeVisible()
  })
  it('shows a new queued command instead of the previous running report', () => {
    render(<UnityStatus state={running} queued unavailable={false} />)
    expect(screen.getByText('명령 대기 중')).toBeVisible()
    expect(screen.getByRole('progressbar')).toHaveAttribute('value', '0')
    expect(screen.getByRole('status')).toHaveTextContent('명령을 전달하고 있습니다.')
  })
  it('shows the error and the message reported by the equipment', () => {
    render(<UnityStatus state={{ ...running, state: 'error', message: '침출 온도 확인 필요' }} queued={false} unavailable={false} />)
    expect(screen.getByText('오류')).toBeVisible()
    expect(screen.getByRole('status')).toHaveTextContent('침출 온도 확인 필요')
  })
})
