import { useEffect, useState } from 'react'

import { analyzeProcess, applyFactory, getFactoryState, getSystemStatus } from './api/client'
import type { AnalysisResult, AnalyzeRequest, FactoryState, SystemStatus as StatusData } from './api/types'
import { SystemStatus } from './components/SystemStatus'
import { AnalysisResults } from './features/dashboard/AnalysisResults'
import { FactoryPanel } from './features/dashboard/FactoryPanel'
import { ProcessForm } from './features/dashboard/ProcessForm'

function App() {
  const [systemStatus, setSystemStatus] = useState<StatusData | null>(null)
  const [connectionFailed, setConnectionFailed] = useState(false)
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [applying, setApplying] = useState(false)
  const [commandQueued, setCommandQueued] = useState(false)
  const [factoryState, setFactoryState] = useState<FactoryState | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getSystemStatus()
      .then(setSystemStatus)
      .catch(() => setConnectionFailed(true))
  }, [])

  useEffect(() => {
    const shouldPoll = commandQueued || factoryState?.state === 'queued' || factoryState?.state === 'running'
    if (!shouldPoll) return

    const timer = window.setTimeout(() => {
      getFactoryState()
        .then((state) => {
          setFactoryState(state)
          setCommandQueued(false)
        })
        .catch((caught: unknown) => {
          setError(caught instanceof Error ? caught.message : '가상 공장 상태 확인에 실패했습니다.')
        })
    }, commandQueued ? 100 : 1000)

    return () => window.clearTimeout(timer)
  }, [commandQueued, factoryState?.state])

  async function handleAnalyze(payload: AnalyzeRequest) {
    setAnalyzing(true)
    setError(null)
    try {
      const result = await analyzeProcess(payload)
      setAnalysis(result)
      setFactoryState(null)
      setCommandQueued(false)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '분석 요청에 실패했습니다.')
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleApply() {
    if (!analysis) return
    setApplying(true)
    setError(null)
    try {
      await applyFactory(analysis.request_id, analysis.recommendation.process_conditions)
      setCommandQueued(true)
      setFactoryState(null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '가상 공장 명령 전송에 실패했습니다.')
    } finally {
      setApplying(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">YOUNGPOONG DIGITAL TWIN</p>
          <h1>습식제련 공정 HMI</h1>
          <p className="subtitle">예측·최적화 결과를 확인하고 가상 공장에 전달하는 B 파트 관제 화면</p>
        </div>
        <SystemStatus status={systemStatus} failed={connectionFailed} />
      </header>

      {error && <div className="error-banner" role="alert">{error}</div>}

      <main className="dashboard-grid">
        <ProcessForm loading={analyzing} onSubmit={handleAnalyze} />
        <div className="right-column">
          <AnalysisResults result={analysis} />
          <FactoryPanel
            canApply={analysis !== null}
            applying={applying}
            queued={commandQueued}
            state={factoryState}
            onApply={handleApply}
          />
        </div>
      </main>

      <footer>현재 A/C 연동은 모의 데이터로 동작하며, 실제 명세 확정 후 어댑터만 교체합니다.</footer>
    </div>
  )
}

export default App
