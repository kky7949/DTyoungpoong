import type { AnalysisResult } from '../../api/types'

interface Props {
  result: AnalysisResult | null
}

export function AnalysisResults({ result }: Props) {
  return (
    <section className="panel results-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">AI ANALYSIS</p>
          <h2>예측 및 최적화 결과</h2>
        </div>
        {result?.source === 'mock' && <span className="mock-badge">모의 데이터</span>}
      </div>
      {!result ? (
        <div className="empty-state">공정 조건을 입력하고 분석을 실행해 주세요.</div>
      ) : (
        <>
          <div className="metric-grid">
            <article className="metric-card">
              <span>현재 니켈 회수율</span>
              <strong>Ni {result.current_prediction.ni_recovery_pct}%</strong>
            </article>
            <article className="metric-card">
              <span>현재 코발트 회수율</span>
              <strong>Co {result.current_prediction.co_recovery_pct}%</strong>
            </article>
          </div>
          <div className="recommendation">
            <h3>추천 운전 조건</h3>
            <dl>
              <div><dt>황산 투입량</dt><dd>{result.recommendation.process_conditions.sulfuric_acid_l} L</dd></div>
              <div>
                <dt className="full-result">추천 침출 온도 {result.recommendation.process_conditions.leaching_temperature_c}°C</dt>
              </div>
              <div><dt>침출 시간</dt><dd>{result.recommendation.process_conditions.leaching_time_hr}시간</dd></div>
            </dl>
          </div>
          <p className="notice">일부 결측값은 AI 전처리 과정에서 보정됩니다.</p>
        </>
      )}
    </section>
  )
}
