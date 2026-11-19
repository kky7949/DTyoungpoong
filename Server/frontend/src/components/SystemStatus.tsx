import type { FactoryState, SystemStatus as SystemStatusData } from '../api/types'

interface Props {
  status: SystemStatusData | null
  failed: boolean
  factoryState: FactoryState | null
  factoryFailed: boolean
}

export function SystemStatus({ status, failed, factoryState, factoryFailed }: Props) {
  const unityConnected = !failed && !factoryFailed && factoryState?.connection_status === 'connected'
  const aReady = !failed && status?.a_adapter === 'live' && status.a_ready === true
  const bConnected = !failed && status !== null
  return (
    <div className="status-strip" aria-label="연동 상태">
      <span className={`status-chip ${aReady ? 'ok' : 'muted'}`}>A {aReady ? '연결' : '미연결'}</span>
      <span className={`status-chip ${failed ? 'failed' : bConnected ? 'ok' : 'muted'}`}>B {bConnected ? '연결' : '미연결'}</span>
      <span className={`status-chip ${unityConnected ? 'ok' : 'muted'}`}>C {unityConnected ? '연결' : '미연결'}</span>
    </div>
  )
}
