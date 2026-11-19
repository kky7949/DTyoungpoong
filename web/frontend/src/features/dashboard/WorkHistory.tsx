import { useEffect, useRef, useState } from 'react'
import type { WorkRecord } from './workHistoryStore'
import { conditionFields, formatDisplayNumber } from './processInput'

const materialFields = [
  ['ni_content_pct', '니켈'], ['co_content_pct', '코발트'], ['li_content_pct', '리튬'],
  ['mn_content_pct', '망간'], ['cu_content_pct', '구리'], ['fe_content_pct', '철'], ['al_content_pct', '알루미늄'],
] as const

export function WorkHistory({ items, warning }: { items: WorkRecord[]; warning: string | null }) {
  const [open, setOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected = items.find((item) => item.commandId === selectedId) ?? items[0] ?? null
  const dialogRef = useRef<HTMLDialogElement>(null)
  const openerRef = useRef<HTMLButtonElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (!open) return
    const dialog = dialogRef.current
    const opener = openerRef.current
    if (!dialog) return
    const previousOverflow = document.body.style.overflow
    dialog.showModal()
    document.body.style.overflow = 'hidden'
    closeRef.current?.focus()
    return () => {
      dialog.close()
      document.body.style.overflow = previousOverflow
      opener?.focus({ preventScroll: true })
    }
  }, [open])
  return <>
    <button ref={openerRef} className="secondary-button history-button" type="button" aria-haspopup="dialog" onClick={() => { setSelectedId(null); setOpen(true) }}>작업 목록</button>
    <dialog ref={dialogRef} className="comparison-dialog history-dialog" aria-labelledby="work-history-heading" onCancel={() => setOpen(false)} onClose={() => setOpen(false)}>
      <div className="dialog-heading"><div><p className="eyebrow">WORK HISTORY</p><h2 id="work-history-heading">작업 목록</h2></div>
        <button ref={closeRef} className="secondary-button" type="button" onClick={() => setOpen(false)}>닫기</button>
      </div>
      {open && <div className="dialog-content">
        <p className="history-scope">현재 브라우저에 저장된 적용 기록 · {items.length}건</p>
        {warning && <p className="history-warning" role="status">{warning}</p>}
        {items.length === 0 ? <p className="history-empty">저장된 작업이 없습니다.</p> : <div className="history-layout">
          <nav className="history-list" aria-label="저장된 작업">{items.map((item) => <button key={item.commandId} type="button" className="history-item" aria-current={item.commandId === selected?.commandId ? 'true' : undefined} onClick={() => setSelectedId(item.commandId)}>
            <strong>{item.input.material.name || '이름 없는 원료'}</strong>
            <time dateTime={item.appliedAt}>{new Date(item.appliedAt).toLocaleString('ko-KR')}</time>
            <span>Ni {formatDisplayNumber(item.prediction.ni_recovery_pct)}% · Co {formatDisplayNumber(item.prediction.co_recovery_pct)}%</span>
          </button>)}</nav>
          {selected && <article className="history-detail">
            <div className="history-detail-heading"><h3>{selected.input.material.name || '이름 없는 원료'}</h3><span>명령 접수 기록</span></div>
            <p className="detail-footnote">저장된 회수율은 전송 당시의 예상값입니다. 실행 완료 여부는 포함하지 않습니다.</p>
            <section className="detail-section" aria-label="저장된 원료 조건"><h3>원료 조건</h3>
              <p className="history-feed">투입량 {selected.input.current_process.feed_amount_kg === null ? '미입력' : `${formatDisplayNumber(selected.input.current_process.feed_amount_kg)} kg`}</p>
              <dl className="material-metrics">{materialFields.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{selected.input.material[key] === null ? '미입력' : `${formatDisplayNumber(selected.input.material[key])}%`}</dd></div>)}</dl>
            </section>
            <section className="detail-section" aria-label="저장된 공정 조건"><h3>적용한 공정 조건</h3>
              <dl className="history-conditions">{conditionFields.map(({ key, label, unit }) => <div key={key}><dt>{label}</dt><dd>{formatDisplayNumber(selected.input.current_process[key])} {unit}</dd></div>)}</dl>
            </section>
            <section className="detail-section" aria-label="저장된 예상 회수율"><h3>적용 조건 예상 회수율</h3>
              <div className="history-recoveries"><div><span>Ni</span><strong>{formatDisplayNumber(selected.prediction.ni_recovery_pct)}%</strong></div><div><span>Co</span><strong>{formatDisplayNumber(selected.prediction.co_recovery_pct)}%</strong></div></div>
            </section>
            <dl className="history-reference"><div><dt>적용 요청 시각</dt><dd><time dateTime={selected.appliedAt}>{new Date(selected.appliedAt).toLocaleString('ko-KR')}</time></dd></div><div><dt>명령 ID</dt><dd>{selected.commandId}</dd></div></dl>
          </article>}
        </div>}
      </div>}
    </dialog>
  </>
}
