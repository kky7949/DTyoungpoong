import type { SystemStatus as SystemStatusData } from '../api/types'

interface Props {
  status: SystemStatusData | null
  failed: boolean
}

function adapterLabel(part: 'A' | 'C', mode: 'mock' | 'live'): string {
  return `${part} ${mode === 'mock' ? '모의 데이터' : '실시간 연결'}`
}

export function SystemStatus({ status, failed }: Props) {
  if (failed) {
    return <div className="connection-error">B 서버에 연결할 수 없습니다.</div>
  }
  if (!status) return <div className="status-loading">서버 연결 확인 중...</div>

  return (
    <div className="status-strip" aria-label="연동 상태">
      <span className="status-chip ok">B 서버 정상</span>
      <span className={`status-chip ${status.a_adapter}`}>{adapterLabel('A', status.a_adapter)}</span>
      <span className={`status-chip ${status.c_adapter}`}>{adapterLabel('C', status.c_adapter)}</span>
      <span className={`status-chip ${status.capabilities.xai ? 'ok' : 'muted'}`}>
        XAI {status.capabilities.xai ? '지원' : '미지원'}
      </span>
    </div>
  )
}
