import { useEffect, useRef, useState, type ReactNode } from 'react'
import type { AnalysisResult, AnalyzeRequest } from '../../api/types'
import { ComparisonDetails } from './ComparisonDetails'
import { conditionFields } from './processInput'

interface Props {
  children?: ReactNode
  result: AnalysisResult | null
  input: AnalyzeRequest | null
  onUseRecommendation?: () => void
  recommendationDisabled?: boolean
  stale?: boolean
  currentPrediction?: AnalysisResult['current_prediction'] | null
  recommendationInput?: AnalyzeRequest | null
}

export function AnalysisResults({ children, result, input, onUseRecommendation, recommendationDisabled, stale, recommendationInput = input, currentPrediction = result?.current_prediction ?? null }: Props) {
  const [comparisonOpen, setComparisonOpen] = useState(false)
  const dialogRef = useRef<HTMLDialogElement>(null)
  const comparisonButton = useRef<HTMLButtonElement>(null)
  const closeButton = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (!comparisonOpen) return
    const dialog = dialogRef.current
    if (!dialog) return
    const opener = comparisonButton.current
    const previousOverflow = document.body.style.overflow
    dialog.showModal()
    document.body.style.overflow = 'hidden'
    closeButton.current?.focus()
    return () => {
      dialog.close()
      document.body.style.overflow = previousOverflow
      opener?.focus({ preventScroll: true })
    }
  }, [comparisonOpen])
  return (
    <section className="panel results-panel" aria-labelledby="analysis-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">AI ANALYSIS</p>
          <h2 id="analysis-heading">{children ? '공정 추천·설정' : 'AI 분석·추천'}</h2>
        </div>
        <div className="analysis-heading-actions">
          {stale && <span className="analysis-status">{result?.source === 'live' ? '원료 또는 목표 변경 · 다시 추천 필요' : '원료 변경 · 다시 추천 필요'}</span>}
          <button ref={comparisonButton} type="button" className="secondary-button comparison-button" aria-haspopup="dialog" onClick={() => setComparisonOpen(true)}>상세 비교 보기</button>
        </div>
      </div>
      <div className="result-content">
          {children ?? (<div className="recommendation-card">
            <h3>{result?.recommendation ? '다음 공정 조건을 추천합니다.' : '원료 조건을 입력하고 추천을 받아보세요.'}</h3>
            <dl className="recommended-values" aria-label="추천 공정 조건">
              {conditionFields.map(({ key, label, unit }) => <div key={key}>
                <dt>{label}</dt><dd><strong>{result?.recommendation?.process_conditions[key] ?? '—'}</strong><span>{unit}</span></dd>
              </div>)}
            </dl>
            <div className="recommended-recovery" role="group" aria-label="추천 조건 예상 회수율">
              <h3>이 조건의 예상 회수율</h3>
              <div className="recommended-recovery-values">
                {([['ni_recovery_pct', '니켈', 'Ni'], ['co_recovery_pct', '코발트', 'Co']] as const).map(([key, label, symbol]) => <div key={key} role="group" aria-label={`${label} 추천 회수율`}>
                  <span>{symbol}</span><strong>{result?.recommendation ? `${result.recommendation.expected_recovery[key]}%` : '—%'}</strong>
                </div>)}
              </div>
            </div>
            <button type="button" className="secondary-button use-recommendation" disabled={!result?.recommendation || !onUseRecommendation || recommendationDisabled} onClick={onUseRecommendation}>추천 조건 사용</button>
          </div>)}
          <dialog ref={dialogRef} className="comparison-dialog" aria-labelledby="comparison-dialog-heading"
            onCancel={() => setComparisonOpen(false)} onClose={() => setComparisonOpen(false)}>
            <div className="dialog-heading"><div><p className="eyebrow">PROCESS COMPARISON</p><h2 id="comparison-dialog-heading">공정 조건 상세 비교</h2></div>
              <button ref={closeButton} className="secondary-button" type="button" onClick={() => setComparisonOpen(false)}>닫기</button></div>
            <div className="dialog-content">
              <ComparisonDetails result={result} input={input} basis={recommendationInput} currentPrediction={currentPrediction} stale={stale} />
            </div>
          </dialog>
      </div>
    </section>
  )
}
