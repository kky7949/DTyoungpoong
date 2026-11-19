import { useEffect, useRef, useState } from 'react'

import { analyzeProcess, ApiRequestError, applyFactory, getFactoryState, getSystemStatus } from './api/client'
import type { FactoryState, RecommendationMode, SystemStatus as StatusData } from './api/types'
import { SystemStatus } from './components/SystemStatus'
import { AnalysisResults } from './features/dashboard/AnalysisResults'
import { UnityStatus } from './features/dashboard/UnityStatus'
import { FactoryPanel } from './features/dashboard/FactoryPanel'
import { WorkHistory } from './features/dashboard/WorkHistory'
import { readWorkHistory, saveWorkHistory, type WorkRecord } from './features/dashboard/workHistoryStore'
import { ProcessForm } from './features/dashboard/ProcessForm'
import { initialProcessInput, toAnalyzeRequest, toRecommendationRequest, processConditionsFromRequest,
  numericFieldErrors, numericFieldFromPath, type NumericInputField, type ProcessInput, type AnalysisSnapshot } from './features/dashboard/processInput'

type ReportedFieldErrors = Partial<Record<NumericInputField, { value: string; message: string }>>

function App() {
  const [systemStatus, setSystemStatus] = useState<StatusData | null>(null)
  const [connectionFailed, setConnectionFailed] = useState(false)
  const [analysisSnapshot, setAnalysisSnapshot] = useState<AnalysisSnapshot | null>(null)
  const [recommendationSnapshot, setRecommendationSnapshot] = useState<AnalysisSnapshot | null>(null)
  const [recommendationMode, setRecommendationMode] = useState<RecommendationMode>('joint')
  const recommendationResult = recommendationSnapshot?.result ?? null
  const analysis = recommendationResult && !recommendationResult.recommendation && recommendationResult.closest_alternative
    ? { ...recommendationResult, recommendation: recommendationResult.closest_alternative }
    : recommendationResult
  const [pendingAction, setPendingAction] = useState<'recommend' | 'predict' | null>(null)
  const analyzing = pendingAction !== null
  const analysisInFlight = useRef(false)
  const [applying, setApplying] = useState(false)
  const [commandQueued, setCommandQueued] = useState(false)
  const [factoryState, setFactoryState] = useState<FactoryState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reportedFieldErrors, setReportedFieldErrors] = useState<ReportedFieldErrors>({})
  const [factoryFailed, setFactoryFailed] = useState(false)
  const [inputValues, setInputValues] = useState<ProcessInput>(initialProcessInput)
  const [initialHistory] = useState(readWorkHistory)
  const [workHistory, setWorkHistory] = useState<WorkRecord[]>(initialHistory.items)
  const [historyWarning, setHistoryWarning] = useState<string | null>(initialHistory.warning)
  const currentInput = toAnalyzeRequest(inputValues)
  const recommendationInput = toRecommendationRequest(currentInput)
  const liveA = systemStatus?.a_adapter === 'live'
  const fieldErrors = numericFieldErrors(inputValues, liveA)
  for (const field of Object.keys(reportedFieldErrors) as NumericInputField[]) {
    const issue = reportedFieldErrors[field]
    if (issue?.value === inputValues[field]) fieldErrors[field] = issue.message
  }
  const hasFieldErrors = Object.keys(fieldErrors).length > 0
  const recommendationFresh = recommendationSnapshot !== null && JSON.stringify(recommendationInput) === JSON.stringify(recommendationSnapshot.input) &&
    (!liveA || recommendationSnapshot.result.mode === recommendationMode)
  const analysisFresh = analysisSnapshot !== null && JSON.stringify(currentInput) === JSON.stringify(analysisSnapshot.input)
  const prediction = analysisFresh ? analysisSnapshot?.result.current_prediction ?? null : null
  const predictionUnavailable = analysisFresh && analysisSnapshot?.result.status === 'PREDICTION_UNUSABLE'
  const validProcess = processConditionsFromRequest(currentInput) !== null
  const factoryGeneration = useRef(0)
  const applyingRef = useRef(false)

  useEffect(() => {
    let stopped = false
    let timer: number | undefined
    async function poll() {
      try {
        const status = await getSystemStatus()
        if (!stopped) { setSystemStatus(status); setConnectionFailed(false) }
      } catch {
        if (!stopped) setConnectionFailed(true)
      } finally {
        if (!stopped) timer = window.setTimeout(poll, 1000)
      }
    }
    void poll()
    return () => { stopped = true; window.clearTimeout(timer) }
  }, [])

  useEffect(() => {
    let stopped = false
    let timer: number | undefined
    async function poll() {
      if (applyingRef.current) {
        if (!stopped) timer = window.setTimeout(poll, 1000)
        return
      }
      const generation = factoryGeneration.current
      try {
        const state = await getFactoryState()
        if (!stopped && generation === factoryGeneration.current && !applyingRef.current) {
          setFactoryState(state)
          setCommandQueued(false)
          setFactoryFailed(false)
        }
      } catch {
        if (!stopped && generation === factoryGeneration.current) setFactoryFailed(true)
      } finally {
        if (!stopped) timer = window.setTimeout(poll, 1000)
      }
    }
    void poll()
    return () => { stopped = true; window.clearTimeout(timer) }
  }, [])

  async function handleAnalysis(action: 'recommend' | 'predict') {
    if (analysisInFlight.current || applyingRef.current) return
    if (action === 'predict' && !validProcess) return
    const submittedInput = structuredClone(action === 'recommend' ? recommendationInput : currentInput)
    analysisInFlight.current = true
    setPendingAction(action)
    setError(null)
    setReportedFieldErrors({})
    try {
      const result = await analyzeProcess(action === 'recommend' && liveA
        ? { ...submittedInput, options: { mode: recommendationMode } }
        : submittedInput)
      if (action === 'recommend') {
        setRecommendationSnapshot({ result, input: submittedInput })
      } else {
        setAnalysisSnapshot({ result, input: submittedInput })
      }
    } catch (caught) {
      if (liveA && action === 'predict') setAnalysisSnapshot(null)
      showRequestError(caught, inputValues, '분석 요청에 실패했습니다.')
    } finally {
      analysisInFlight.current = false
      setPendingAction(null)
    }
  }

  function showRequestError(caught: unknown, submittedValues: ProcessInput, fallback: string) {
    if (caught instanceof ApiRequestError && caught.status === 422 && caught.details.length) {
      const issues: ReportedFieldErrors = {}
      const generalMessages: string[] = []
      for (const detail of caught.details) {
        const field = numericFieldFromPath(detail.field)
        if (field) issues[field] = { value: submittedValues[field], message: detail.message }
        else generalMessages.push(detail.message)
      }
      setReportedFieldErrors(issues)
      setError(generalMessages.length ? [caught.summary, ...generalMessages].join(' ') : null)
      return
    }
    setError(caught instanceof Error ? caught.message : fallback)
  }

  async function handleApply() {
    const conditions = analysisSnapshot && processConditionsFromRequest(analysisSnapshot.input)
    if (!analysisSnapshot || !prediction || !conditions || hasFieldErrors || analyzing || factoryFailed || connectionFailed || !factoryState || applyingRef.current || commandQueued || factoryState.state === 'queued' || factoryState.state === 'running') return
    applyingRef.current = true
    // 적용 전에 시작한 상태 응답이 새 명령의 대기 상태를 덮지 못하게 한다.
    factoryGeneration.current += 1
    setApplying(true)
    setError(null)
    try {
      const accepted = await applyFactory({
        analysis_request_id: analysisSnapshot.result.request_id,
        material: {
          ...analysisSnapshot.input.material,
          feed_amount_kg: analysisSnapshot.input.current_process.feed_amount_kg,
        },
        process_conditions: conditions,
        expected_recovery: prediction,
      })
      setCommandQueued(true)
      setFactoryState(null)
      const entry: WorkRecord = {
        commandId: accepted.command_id,
        appliedAt: new Date().toISOString(),
        analysisRequestId: analysisSnapshot.result.request_id,
        source: analysisSnapshot.result.source,
        input: structuredClone(analysisSnapshot.input),
        prediction: structuredClone(prediction),
      }
      const nextHistory = [entry, ...workHistory.filter((item) => item.commandId !== entry.commandId)]
      setWorkHistory(nextHistory)
      try {
        saveWorkHistory(nextHistory)
        setHistoryWarning(null)
      } catch {
        setHistoryWarning('명령은 접수됐지만 작업 기록을 브라우저에 저장하지 못했습니다. 새 기록은 현재 화면에서만 확인할 수 있습니다.')
      }
    } catch (caught) {
      showRequestError(caught, inputValues, '가상 공장 명령 전송에 실패했습니다.')
    } finally {
      applyingRef.current = false
      setApplying(false)
    }
  }

  const factoryBusy = commandQueued || factoryState?.state === 'queued' || factoryState?.state === 'running'
  const canApply = prediction !== null && validProcess && !hasFieldErrors && !analyzing && factoryState !== null &&
    !factoryFailed && !connectionFailed && !factoryBusy
  const applyBlockedReason = applying ? '명령을 전송하고 있습니다.' : analyzing ? '분석이 끝나면 적용할 수 있습니다.' :
    factoryBusy ? (factoryState?.state === 'queued' && factoryState.connection_status === 'disconnected'
      ? 'Unity 미연결로 이전 명령이 대기 중입니다.'
      : '이전 공정이 대기·실행 중입니다. 완료 후 적용할 수 있습니다.') :
    !validProcess ? '추천 조건을 사용하거나 공정 조건을 입력해 주세요.' :
    predictionUnavailable ? (analysisSnapshot?.result.warnings?.includes('DISTANCE_REVIEW')
      ? 'A 모델이 지원하는 범위를 벗어난 조건입니다. 값을 조정한 뒤 다시 예측해 주세요.'
      : '이 조건의 회수율을 표시할 수 없습니다. 값을 조정한 뒤 다시 예측해 주세요.') :
    !prediction ? (analysisSnapshot ? '조건이 변경되었습니다. ‘회수율 예측’을 다시 눌러 주세요.' : '‘회수율 예측’을 눌러 예상 회수율을 확인해 주세요.') :
    connectionFailed || factoryFailed ? '서버 상태를 확인할 수 없습니다. 연결 복구 후 적용할 수 있습니다.' :
    !factoryState ? '공정 상태를 확인하고 있습니다.' :
    null

  function loadRecommendation() {
    if (!analysis?.recommendation || !recommendationSnapshot || !recommendationFresh || analysisInFlight.current || applyingRef.current) return
    const conditions = analysis.recommendation.process_conditions
    setReportedFieldErrors({})
    setInputValues((values) => ({ ...values, sulfuric_acid_l: String(conditions.sulfuric_acid_l),
      leaching_temperature_c: String(conditions.leaching_temperature_c),
      leaching_time_hr: String(conditions.leaching_time_hr) }))
    // A가 해당 추천 조건에 대해 반환한 예상 회수율을 사용한다.
    setAnalysisSnapshot({
      input: {
        ...recommendationSnapshot.input,
        current_process: { ...recommendationSnapshot.input.current_process, ...conditions },
      },
      result: { ...analysis, current_prediction: analysis.recommendation.expected_recovery },
    })
    document.getElementById('process-condition-heading')?.focus({ preventScroll: true })
  }

  function changeInput(key: keyof ProcessInput, value: string) {
    setInputValues((values) => ({ ...values, [key]: value }))
    if (key !== 'name') setReportedFieldErrors((issues) => {
      if (!issues[key]) return issues
      const remaining = { ...issues }
      delete remaining[key]
      return remaining
    })
  }

  function startNewWork() {
    if (analysisInFlight.current || applyingRef.current) return
    setInputValues(initialProcessInput)
    setRecommendationSnapshot(null)
    setRecommendationMode('joint')
    setAnalysisSnapshot(null)
    setError(null)
    setReportedFieldErrors({})
    document.getElementById('material-name')?.focus({ preventScroll: true })
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">YOUNGPOONG DIGITAL TWIN</p>
          <h1>금속 회수율 최적화 대시보드</h1>
        </div>
        <div className="control-assembly">
          <div className="chassis-vents" aria-hidden="true" />
          <SystemStatus status={systemStatus} failed={connectionFailed} factoryState={factoryState} factoryFailed={factoryFailed} />
        </div>
      </header>

      {error && <div className="error-banner" role="alert">{error}</div>}
      {historyWarning && <div className="history-warning" role="status">{historyWarning}</div>}

      <main className="dashboard-grid">
        <ProcessForm locked={applying} values={inputValues} fieldErrors={fieldErrors} onChange={changeInput}
          onRecommend={() => handleAnalysis('recommend')} busy={analyzing} recommending={pendingAction === 'recommend'}
          recommendationMode={recommendationMode} recommendationModeEnabled={liveA && !connectionFailed}
          onModeChange={setRecommendationMode} />
        <div className="results-column">
          <AnalysisResults result={analysis} input={recommendationFresh ? currentInput : null} recommendationInput={recommendationSnapshot?.input ?? null}
            currentPrediction={recommendationFresh ? prediction : null}
            stale={analysis !== null && !recommendationFresh}>
            <FactoryPanel
            recommendation={analysis}
            onUseRecommendation={loadRecommendation}
            recommendationDisabled={analyzing || applying || !recommendationFresh}
            canApply={canApply} onApply={handleApply} applyBlockedReason={applyBlockedReason}
            applying={applying}
            values={inputValues}
            fieldErrors={fieldErrors}
            onChange={changeInput}
            onAnalyze={() => handleAnalysis('predict')}
            analyzing={pendingAction === 'predict'}
            busy={analyzing}
            canPredict={validProcess}
            prediction={prediction}
          />
          </AnalysisResults>
        </div>
        <UnityStatus queued={commandQueued} state={factoryState} unavailable={factoryFailed}
          historyAction={<WorkHistory items={workHistory} warning={historyWarning} />}
          onNewWork={startNewWork} resetDisabled={analyzing || applying} />
      </main>

    </div>
  )
}

export default App
