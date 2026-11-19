import { useEffect, useState, type CSSProperties } from 'react'
import { createPortal } from 'react-dom'

export function InputIssue({ id, label, message }: { id: string; label: string; message: string }) {
  const [position, setPosition] = useState<CSSProperties | null>(null)

  function show(button: HTMLButtonElement) {
    const rect = button.getBoundingClientRect()
    const width = Math.min(248, window.innerWidth - 16)
    const left = Math.min(Math.max(8, rect.right - width), window.innerWidth - width - 8)
    const above = window.innerHeight - rect.bottom < 84
    setPosition({ width, left, top: above ? rect.top - 6 : rect.bottom + 6,
      transform: above ? 'translateY(-100%)' : undefined })
  }

  useEffect(() => {
    if (!position) return
    const dismiss = () => setPosition(null)
    window.addEventListener('scroll', dismiss, true)
    window.addEventListener('resize', dismiss)
    return () => {
      window.removeEventListener('scroll', dismiss, true)
      window.removeEventListener('resize', dismiss)
    }
  }, [position])

  return <>
    <button className="input-issue" type="button" aria-label={`${label} 오류`} aria-describedby={id}
      onMouseEnter={(event) => show(event.currentTarget)} onMouseLeave={() => setPosition(null)}
      onFocus={(event) => show(event.currentTarget)} onBlur={() => setPosition(null)}
      onClick={(event) => show(event.currentTarget)}
      onKeyDown={(event) => { if (event.key === 'Escape') setPosition(null) }}>!</button>
    {createPortal(<span id={id} className="input-issue-tooltip" role="tooltip"
      hidden={position === null} style={position ?? undefined}>{message}</span>, document.body)}
  </>
}
