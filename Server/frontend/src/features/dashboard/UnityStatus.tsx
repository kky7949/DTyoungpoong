import type { ReactNode } from 'react'
import type { FactoryState } from '../../api/types'
import { formatDisplayNumber } from './processInput'

const stateLabels: Record<FactoryState['state'], string> = {
  disconnected: '연결 끊김', idle: '대기', queued: '명령 대기 중', running: '실행 중', completed: '완료', error: '오류',
}
export function UnityStatus({ queued, state, unavailable, onNewWork, resetDisabled, historyAction }: {
  queued: boolean
  state: FactoryState | null
  unavailable: boolean
  onNewWork?: () => void
  resetDisabled?: boolean
  historyAction?: ReactNode
}) {
  const stateText = queued ? '명령 대기 중' : !state ? '상태 확인 중' :
    state.state === 'running' ? `${stateLabels[state.state]} · ${formatDisplayNumber(state.progress_pct)}%` : stateLabels[state.state]
  const connected = !unavailable && state?.connection_status === 'connected'
  const historical = unavailable || state?.connection_status === 'disconnected'
  const progress = queued ? 0 : state?.command_id ? state.progress_pct : null
  const progressText = progress === null ? undefined : `${formatDisplayNumber(progress)}%`
  const tone = unavailable ? 'unknown' : !connected ? 'offline' : queued ? 'queued' : state?.state ?? 'unknown'
  return <section className={`panel unity-status state-${tone}${onNewWork ? ' has-work-action' : ''}`} aria-label="Unity 가상 공장">
    <div className="equipment-identity">
      <span className="equipment-icon" aria-hidden="true">DT</span>
      <div><p className="eyebrow">EQUIPMENT STATUS</p><h3>Unity 가상 공장</h3>
        <span className={`equipment-link ${connected ? 'connected' : 'offline'}`}>
          {unavailable ? '상태 조회 실패' : !state ? '연결 확인 중' : connected ? '연결됨' : '연결 끊김'}
        </span>
      </div>
    </div>
    <div className="equipment-operation">
      <div className="equipment-progress-heading"><span>{historical ? '마지막 확인 상태' : '공정 상태'}</span><p className="factory-state">{stateText}</p></div>
      {progress === null ? <div className="equipment-progress-placeholder">{state?.state === 'idle' ? '실행할 공정을 기다리고 있습니다.' : '진행률 보고 대기'}</div> :
        <progress className="equipment-progress" max={100} value={progress} aria-label={historical ? '마지막 확인 공정 진행률' : '공정 진행률'}
          aria-valuetext={progressText}>{progressText}</progress>}
      {progress !== null && (queued || state?.state !== 'running') && <span className="equipment-progress-value">{progressText}</span>}
    </div>
    <div className="equipment-report">
      <span className="report-label">{historical ? '마지막 보고' : '설비 메시지'}</span>
      <p className="equipment-message" role="status">{unavailable ? '공정 상태를 확인할 수 없습니다. 자동 재시도 중입니다.' : queued ? '명령을 전달하고 있습니다.' : state?.message || '설비 보고 대기'}</p>
      <p className="equipment-last-seen">마지막 통신 <time dateTime={state?.last_seen_at ?? undefined}>{state?.last_seen_at ? new Date(state.last_seen_at).toLocaleString('ko-KR') : '없음'}</time></p>
      {historical && state?.command_id && <p className="equipment-history-note">공정 상태와 진행률은 마지막 보고 기준입니다.</p>}
    </div>
    {onNewWork && <div className="equipment-actions">
      <div className="equipment-action-buttons" role="group" aria-label="가상 공장 작업">
        {historyAction}
        {onNewWork && <button className="secondary-button new-work-button" type="button" disabled={resetDisabled} onClick={onNewWork} title="입력과 분석 결과를 비웁니다. Unity 실행 상태는 유지됩니다.">새 작업 시작</button>}
      </div>
    </div>}
  </section>
}
