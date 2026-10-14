import type { FactoryState } from '../../api/types'

interface Props {
  canApply: boolean
  applying: boolean
  queued: boolean
  state: FactoryState | null
  onApply: () => void
}

const stateLabels: Record<FactoryState['state'], string> = {
  disconnected: '연결 끊김',
  idle: '대기',
  queued: '명령 대기 중',
  running: '실행 중',
  completed: '완료',
  error: '오류',
}

export function FactoryPanel({ canApply, applying, queued, state, onApply }: Props) {
  let stateText = '분석 결과를 먼저 생성해 주세요.'
  if (queued) stateText = '명령 대기 중'
  if (state) {
    stateText = state.state === 'running'
      ? `${stateLabels[state.state]} · ${state.progress_pct}%`
      : stateLabels[state.state]
  }

  return (
    <section className="panel factory-panel">
      <div>
        <p className="eyebrow">DIGITAL TWIN</p>
        <h2>Unity 가상 공장</h2>
        <p className="factory-state">{stateText}</p>
      </div>
      <button className="secondary-button" type="button" disabled={!canApply || applying} onClick={onApply}>
        {applying ? '명령 전송 중...' : '가상 공장에 적용'}
      </button>
    </section>
  )
}
