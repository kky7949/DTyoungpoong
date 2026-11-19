import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../../App'
import { readWorkHistory } from './workHistoryStore'

const analysisResult = {
  schema_version: 'draft-1', source: 'mock', generated_at: '2026-11-03T00:00:00Z', request_id: 'recommend-123',
  current_prediction: { ni_recovery_pct: 85.65, co_recovery_pct: 78.45 },
  recommendation: {
    process_conditions: { sulfuric_acid_l: 1050, leaching_temperature_c: 62, leaching_time_hr: 5.5 },
    expected_recovery: { ni_recovery_pct: 89.2, co_recovery_pct: 82.1 },
  },
}
const idle = {
  source: 'mock', state: 'idle', command_id: null, progress_pct: 0, message: '',
  updated_at: '2026-11-03T00:00:00Z', connection_status: 'connected', last_seen_at: '2026-11-03T00:00:00Z',
}
const running = { ...idle, state: 'running', command_id: 'command-123', progress_pct: 35 }
function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}
function defaultFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = String(input)
  if (url.endsWith('/health')) return Promise.resolve(jsonResponse({ status: 'ok' }))
  if (url.endsWith('/system/status')) return Promise.resolve(jsonResponse({
    backend: 'ok', a_adapter: 'mock', c_adapter: 'mock',
    capabilities: { prediction: true, optimization: true, xai: false, unity_control: true },
  }))
  if (url.endsWith('/process/analyze')) return Promise.resolve(jsonResponse(analysisResult))
  if (url.endsWith('/factory/state')) return Promise.resolve(jsonResponse(idle))
  if (url.endsWith('/factory/apply')) return Promise.resolve(jsonResponse({ command_id: 'command-123', status: 'queued', source: 'mock' }, 202))
  return Promise.reject(new Error(`Unexpected request: ${url} ${init?.method}`))
}
async function recommend() {
  fireEvent.click(screen.getByRole('button', { name: '최적 공정 추천' }))
  await waitFor(() => expect(screen.getByRole('button', { name: '최적 공정 추천' })).toBeEnabled())
}
async function prepare() {
  await screen.findByText('B 연결')
  change('원료 이름', '혼합 원료 A')
  change('니켈 함량 (%)', '12.17')
  change('원료 투입량 (kg)', '1000')
  await recommend()
  fireEvent.click(screen.getByRole('button', { name: '추천값 적용하기' }))
}
async function predict() {
  fireEvent.click(screen.getByRole('button', { name: '회수율 예측' }))
  await waitFor(() => expect(screen.getByRole('button', { name: '회수율 예측' })).toBeEnabled())
}
function change(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } })
}
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); vi.restoreAllMocks(); localStorage.clear() })

describe('material-first recommendation workflow', () => {
  it('shows and applies the live alternative in the recommendation table and blocks unusable predictions', async () => {
    const candidate = analysisResult.recommendation
    const alternative = { process_conditions: { sulfuric_acid_l: 1500, leaching_temperature_c: 95, leaching_time_hr: 7 },
      expected_recovery: { ni_recovery_pct: 91.21, co_recovery_pct: 83.45 } }
    const common = { ...analysisResult, source: 'live', current_prediction: null, recommendation: null }
    const fetchMock = vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/system/status')) return Promise.resolve(jsonResponse({
        backend: 'ok', a_adapter: 'live', a_ready: true, c_adapter: 'mock',
      }))
      if (String(url).endsWith('/process/analyze')) {
        const payload = JSON.parse(String(init?.body))
        if (payload.options?.mode === 'joint') return Promise.resolve(jsonResponse({
          ...common, status: 'TARGET_NOT_FOUND_IN_GRID', mode: 'joint', closest_alternative: alternative,
        }))
        if (payload.options?.mode === 'ni') return Promise.resolve(jsonResponse({
          ...common, status: 'RECOMMENDED_ON_PREDICTION', mode: 'ni', recommendation: candidate,
        }))
        return Promise.resolve(jsonResponse({ ...common, status: 'PREDICTION_UNUSABLE', warnings: ['DISTANCE_REVIEW'] }))
      }
      return defaultFetch(url, init)
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    const goal = screen.getByRole('combobox', { name: '추천 목표' })
    expect(goal).toBeDisabled()
    await screen.findByText('A 연결')
    expect(screen.getByRole('combobox', { name: '추천 목표' })).toBe(goal)
    expect(goal).toBeEnabled()
    expect(within(goal).getAllByRole('option').map((option) => option.textContent))
      .toEqual(['동시 회수율 최대', '니켈 회수율 최대', '코발트 회수율 최대'])
    await recommend()
    const table = within(screen.getByRole('table', { name: '추천 공정 조건' }))
    expect(table.getByRole('columnheader', { name: 'AI 추천값' })).toBeVisible()
    expect(screen.queryByText(/목표 미달 대안/)).not.toBeInTheDocument()
    expect(table.getByText('1500')).toBeVisible()
    expect(screen.getByRole('group', { name: '추천 조건 예상 회수율' })).toHaveTextContent('91.21%')
    expect(screen.queryByText(/목표를 충족하는 공정 조건을 찾지 못했습니다/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '추천값 적용하기' }))
    expect(screen.getByLabelText('황산 투입량 (L)')).toHaveValue(1500)
    expect(screen.getByLabelText('침출 온도 (°C)')).toHaveValue(95)
    expect(screen.getByLabelText('침출 시간 (시간)')).toHaveValue(7)
    expect(screen.getByRole('group', { name: '입력 조건 예상 회수율' })).toHaveTextContent('83.45%')
    change('추천 목표', 'ni')
    await recommend()
    expect(table.getByRole('columnheader', { name: 'AI 추천값' })).toBeVisible()
    expect(table.getByText('1050')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: '추천값 적용하기' }))
    await predict()
    expect(screen.getByText(/A 모델이 지원하는 범위를 벗어난 조건/)).toBeVisible()
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
  })
  it('keeps accepted work visible for this session when browser persistence fails', async () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new DOMException('Quota exceeded', 'QuotaExceededError') })
    vi.stubGlobal('fetch', vi.fn(defaultFetch))
    render(<App />)
    await prepare()
    fireEvent.click(screen.getByRole('button', { name: '가상 공장에 적용' }))
    await screen.findByText('명령 대기 중')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByText(/명령은 접수됐지만 작업 기록을 브라우저에 저장하지 못했습니다/)).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: '작업 목록' }))
    expect(within(screen.getByRole('dialog')).getByRole('button', { name: /혼합 원료 A/ })).toBeVisible()
  })
  it('saves accepted work, retains its submitted values after reset and reload, and opens read-only history', async () => {
    let applied = 0
    const recommendation = {
      process_conditions: { ...analysisResult.recommendation.process_conditions, sulfuric_acid_l: 1050.123456 },
      expected_recovery: { ni_recovery_pct: 89.23456, co_recovery_pct: 82.12345 },
    }
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/factory/apply')) applied += 1
      if (String(url).endsWith('/process/analyze')) return Promise.resolve(jsonResponse({ ...analysisResult, recommendation }))
      return defaultFetch(url, init)
    }))
    const view = render(<App />)
    fireEvent.click(screen.getByRole('button', { name: '작업 목록' }))
    expect(screen.getByText('저장된 작업이 없습니다.')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: '닫기' }))
    change('코발트 함량 (%)', '6.56789')
    await prepare()
    fireEvent.click(screen.getByRole('button', { name: '가상 공장에 적용' }))
    await screen.findByText('명령 대기 중')
    expect(applied).toBe(1)
    fireEvent.click(screen.getByRole('button', { name: '새 작업 시작' }))
    view.unmount()
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: '작업 목록' }))
    const dialog = screen.getByRole('dialog', { name: '작업 목록' })
    const record = within(dialog).getByRole('button', { name: /혼합 원료 A/ })
    expect(record).toHaveTextContent('Ni 89.23% · Co 82.12%')
    fireEvent.click(record)
    expect(within(dialog).getByRole('region', { name: '저장된 원료 조건' })).toHaveTextContent('6.57%')
    expect(within(dialog).getByRole('region', { name: '저장된 공정 조건' })).toHaveTextContent('1050.12 L')
    expect(within(dialog).getByRole('region', { name: '저장된 예상 회수율' })).toHaveTextContent('89.23%')
    expect(readWorkHistory().items[0].prediction).toEqual(recommendation.expected_recovery)
    expect(within(dialog).getByText('명령 접수 기록')).toBeVisible()
    expect(within(dialog).queryByRole('spinbutton')).not.toBeInTheDocument()
    expect(applied).toBe(1)
    fireEvent.click(within(dialog).getByRole('button', { name: '닫기' }))
    expect(screen.getByRole('button', { name: '작업 목록' })).toHaveFocus()
  })
  it('does not save failed applications', async () => {
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/factory/apply')) return Promise.resolve(jsonResponse({ error: { message: '명령 등록 실패' } }, 503))
      return defaultFetch(url, init)
    }))
    render(<App />)
    await prepare()
    fireEvent.click(screen.getByRole('button', { name: '가상 공장에 적용' }))
    await screen.findByRole('alert')
    fireEvent.click(screen.getByRole('button', { name: '작업 목록' }))
    expect(screen.getByText('저장된 작업이 없습니다.')).toBeVisible()
  })
  it('starts a blank work item without changing Unity execution or sending a command', async () => {
    const fetchMock = vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/factory/state')) return Promise.resolve(jsonResponse(running))
      return defaultFetch(url, init)
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    await prepare()
    const postCount = () => fetchMock.mock.calls.filter(([, init]) => init?.method === 'POST').length
    const previousPosts = postCount()
    expect(within(screen.getByRole('region', { name: '공정 추천·설정' })).queryByRole('button', { name: '새 작업 시작' })).not.toBeInTheDocument()
    expect(screen.queryByText('추천 완료')).not.toBeInTheDocument()
    fireEvent.click(within(screen.getByRole('region', { name: 'Unity 가상 공장' })).getByRole('button', { name: '새 작업 시작' }))
    expect(screen.getByLabelText('원료 이름')).toHaveValue('')
    expect(screen.getByLabelText('원료 이름')).toHaveFocus()
    for (const input of screen.getAllByRole('spinbutton')) expect(input).toHaveValue(null)
    expect(within(screen.getByLabelText('추천 공정 조건')).queryByText('1050')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '추천값 적용하기' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
    expect(screen.getByRole('group', { name: '입력 조건 예상 회수율' })).not.toHaveTextContent('89.2%')
    expect(screen.getByText('실행 중 · 35%')).toBeVisible()
    expect(postCount()).toBe(previousPosts)
    change('원료 이름', '새 원료')
    await recommend()
    expect(screen.getByRole('button', { name: '추천값 적용하기' })).toBeEnabled()
  })
  it('prevents a reset during an analysis and allows it after the request fails', async () => {
    let resolve!: (response: Response) => void
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/process/analyze')) return new Promise<Response>((done) => { resolve = done })
      return defaultFetch(url, init)
    }))
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: '최적 공정 추천' }))
    expect(screen.getByRole('button', { name: '새 작업 시작' })).toBeDisabled()
    await act(async () => { resolve(jsonResponse({ error: { message: '분석 실패' } }, 502)) })
    expect(screen.getByRole('alert')).toHaveTextContent('분석 실패')
    fireEvent.click(screen.getByRole('button', { name: '새 작업 시작' }))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByLabelText('원료 이름')).toHaveValue('')
  })
  it('places each recommendation beside its editable condition in one workspace', async () => {
    vi.stubGlobal('fetch', vi.fn(defaultFetch))
    render(<App />)
    await recommend()
    const workspace = screen.getByRole('region', { name: '공정 추천·설정' })
    const workActions = within(workspace).getByRole('group', { name: '공정 조건 작업' })
    expect(within(workActions).getByRole('button', { name: '추천값 적용하기' })).toBeVisible()
    expect(within(workActions).getByRole('button', { name: '회수율 예측' })).toBeVisible()
    const factoryActions = within(screen.getByRole('region', { name: 'Unity 가상 공장' })).getByRole('group', { name: '가상 공장 작업' })
    expect(within(factoryActions).queryByRole('button', { name: '가상 공장에 적용' })).not.toBeInTheDocument()
    expect(within(workspace).getByRole('button', { name: '가상 공장에 적용' })).toBeVisible()
    expect(within(factoryActions).getByRole('button', { name: '새 작업 시작' })).toBeVisible()
    const table = within(workspace).getByRole('table', { name: '추천 공정 조건' })
    const acid = within(table).getByRole('row', { name: /황산 투입량/ })
    expect(within(acid).getByText('1050')).toBeVisible()
    expect(within(acid).getByLabelText('황산 투입량 (L)')).toHaveValue(null)
    fireEvent.click(within(workspace).getByRole('button', { name: '추천값 적용하기' }))
    expect(within(acid).getByLabelText('황산 투입량 (L)')).toHaveValue(1050)
    change('황산 투입량 (L)', '1200')
    expect(within(acid).getByText('1050')).toBeVisible()
    expect(within(acid).getByLabelText('황산 투입량 (L)')).toHaveValue(1200)
    expect(within(workspace).getByRole('group', { name: '추천 조건 예상 회수율' })).toHaveTextContent('89.2%')
    expect(within(workspace).getByRole('group', { name: '입력 조건 예상 회수율' })).not.toHaveTextContent('89.2%')
    expect(within(workspace).getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
    expect(within(screen.getByRole('region', { name: 'Unity 가상 공장' })).queryByRole('button', { name: '가상 공장에 적용' })).not.toBeInTheDocument()
    expect(within(workspace).getByText('조건이 변경되었습니다. ‘회수율 예측’을 다시 눌러 주세요.')).toBeVisible()
    expect(screen.getAllByText('조건이 변경되었습니다. ‘회수율 예측’을 다시 눌러 주세요.')).toHaveLength(1)
    expect(screen.queryByText('조건 변경됨 · 재예측 필요')).not.toBeInTheDocument()
    expect(screen.queryByText('예측 확인됨')).not.toBeInTheDocument()
    expect(screen.getByRole('region', { name: '원료 조건' })).toBeVisible()
  })
  it('compares draft conditions but hides recovery predictions until they match, and preserves the recommendation basis', async () => {
    vi.stubGlobal('fetch', vi.fn(defaultFetch))
    render(<App />)
    await prepare()
    change('황산 투입량 (L)', '1200')
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    expect(within(screen.getByRole('dialog')).getByRole('row', { name: /황산 투입량/ })).toHaveTextContent('1200 L')
    expect(screen.queryByRole('meter', { name: '니켈 현재 조건 예상 회수율' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '닫기' }))
    change('니켈 함량 (%)', '20')
    await predict()
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    expect(within(screen.getByRole('dialog')).getByText('12.17%')).toBeVisible()
    expect(screen.queryByRole('meter', { name: '니켈 현재 조건 예상 회수율' })).not.toBeInTheDocument()
  })
  it('shows both input groups together and retains values when editing either group', () => {
    vi.stubGlobal('fetch', vi.fn(defaultFetch))
    render(<App />)
    expect(screen.queryByRole('tablist')).not.toBeInTheDocument()
    expect(screen.getByRole('region', { name: '원료 조건' })).toBeVisible()
    expect(screen.getByRole('region', { name: '공정 조건 설정' })).toBeVisible()
    change('니켈 함량 (%)', '15')
    change('황산 투입량 (L)', '900')
    expect(screen.getByLabelText('니켈 함량 (%)')).toHaveValue(15)
    expect(screen.getByLabelText('황산 투입량 (L)')).toHaveValue(900)
    expect(screen.getByRole('region', { name: 'Unity 가상 공장' })).toBeVisible()
  })
  it('shows model range placeholders in empty material fields and allows recommendation', () => {
    vi.stubGlobal('fetch', vi.fn(defaultFetch))
    render(<App />)
    const material = screen.getByRole('region', { name: '원료 조건' })
    for (const [label, range] of [
      ['니켈 함량 (%)', '8~30'], ['코발트 함량 (%)', '2~15'],
      ['리튬 함량 (%)', '2~6'], ['망간 함량 (%)', '5~16'],
      ['구리 불순물 (%)', '0.3~6'], ['철 불순물 (%)', '0.2~6'],
      ['알루미늄 불순물 (%)', '0.5~7'], ['원료 투입량 (kg)', '80~200'],
    ]) {
      const input = within(material).getByRole('spinbutton', { name: label })
      expect(input).toHaveAttribute('placeholder', range)
      expect(input).toHaveAccessibleDescription(range)
    }
    expect(within(material).getByLabelText('원료 이름')).toHaveValue('')
    for (const input of within(material).getAllByRole('spinbutton')) expect(input).toHaveValue(null)
    expect(within(material).getByLabelText('알루미늄 불순물 (%)')).toBeInTheDocument()
    expect(within(material).getByRole('button', { name: '최적 공정 추천' })).toBeEnabled()
    const process = screen.getByRole('region', { name: '공정 조건 설정' })
    expect(within(process).queryByLabelText('원료 투입량 (kg)')).not.toBeInTheDocument()
    for (const label of ['황산 투입량 (L)', '침출 온도 (°C)', '침출 시간 (시간)']) {
      expect(within(process).getByLabelText(label)).toHaveValue(null)
    }
    expect(screen.getByRole('button', { name: '회수율 예측' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
  })
  it('shows A B C in order without removed labels', async () => {
    vi.stubGlobal('fetch', vi.fn(defaultFetch))
    render(<App />)
    await screen.findByText('B 연결')
    expect(screen.getByLabelText('연동 상태').textContent).toBe('A 미연결B 연결C 연결')
    expect(screen.getByRole('combobox', { name: '추천 목표' })).toBeDisabled()
    expect(screen.queryByText(/XAI|임시 명세|모의 데이터|원료 등급|마지막 전송 조건/)).not.toBeInTheDocument()
  })
  it('sends only material and feed for recommendation even when process fields have values', async () => {
    let body: unknown
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/process/analyze')) body = JSON.parse(String(init?.body))
      return defaultFetch(url, init)
    }))
    render(<App />)
    change('리튬 함량 (%)', '0')
    change('원료 투입량 (kg)', '1000')
    change('황산 투입량 (L)', '1200')
    change('침출 온도 (°C)', '80')
    change('침출 시간 (시간)', '7')
    await recommend()
    expect(body).toMatchObject({
      material: { name: null, ni_content_pct: null, co_content_pct: null, li_content_pct: 0, mn_content_pct: null, cu_content_pct: null, fe_content_pct: null, al_content_pct: null },
      current_process: { feed_amount_kg: 1000, sulfuric_acid_l: null, leaching_temperature_c: null, leaching_time_hr: null },
    })
    expect(screen.getByRole('group', { name: '추천 조건 예상 회수율' })).toHaveTextContent('89.2%')
    expect(within(screen.getByRole('group', { name: '입력 조건 예상 회수율' })).queryByText('85.65%')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '상세 비교 보기' }))
    expect(screen.queryByRole('meter', { name: '니켈 현재 조건 예상 회수율' })).not.toBeInTheDocument()
  })
  it('passes every added material content to the adapter request', async () => {
    let body: unknown
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/process/analyze')) body = JSON.parse(String(init?.body))
      return defaultFetch(url, init)
    }))
    render(<App />)
    for (const [label, value] of [
      ['리튬 함량 (%)', '4.25'], ['망간 함량 (%)', '10.49'], ['구리 불순물 (%)', '1.9'],
      ['철 불순물 (%)', '2.04'], ['알루미늄 불순물 (%)', '3.43'],
    ]) change(label, value)
    await recommend()
    expect(body).toMatchObject({ material: { li_content_pct: 4.25, mn_content_pct: 10.49, cu_content_pct: 1.9, fe_content_pct: 2.04, al_content_pct: 3.43 } })
  })
  it('uses the recommendation and its expected recovery without predicting null process inputs', async () => {
    let applied: unknown
    let analyses = 0
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/process/analyze')) analyses += 1
      if (String(url).endsWith('/factory/apply')) applied = JSON.parse(String(init?.body))
      return defaultFetch(url, init)
    }))
    render(<App />)
    change('코발트 함량 (%)', '2.41')
    change('리튬 함량 (%)', '0')
    change('망간 함량 (%)', '10.49')
    change('구리 불순물 (%)', '1.9')
    change('알루미늄 불순물 (%)', '3.43')
    await prepare()
    expect(analyses).toBe(1)
    expect(screen.getByLabelText('황산 투입량 (L)')).toHaveValue(1050)
    expect(screen.getByLabelText('침출 온도 (°C)')).toHaveValue(62)
    expect(screen.getByLabelText('침출 시간 (시간)')).toHaveValue(5.5)
    const prediction = screen.getByRole('group', { name: '입력 조건 예상 회수율' })
    expect(prediction).toHaveTextContent('89.2%')
    expect(prediction).not.toHaveTextContent('85.65%')
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: '공정 조건 설정' }))
    fireEvent.click(screen.getByRole('button', { name: '가상 공장에 적용' }))
    await screen.findByText('명령 대기 중')
    expect(applied).toEqual({ analysis_request_id: 'recommend-123', process_conditions: analysisResult.recommendation.process_conditions,
      material: { name: '혼합 원료 A', feed_amount_kg: 1000, ni_content_pct: 12.17, co_content_pct: 2.41,
        li_content_pct: 0, mn_content_pct: 10.49, cu_content_pct: 1.9, fe_content_pct: null, al_content_pct: 3.43 },
      expected_recovery: analysisResult.recommendation.expected_recovery })
  })
  it('predicts edited process values without replacing the material-only recommendation', async () => {
    let attempt = 0
    let body: unknown
    let applied: unknown
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/process/analyze') && ++attempt === 2) {
        body = JSON.parse(String(init?.body))
        return Promise.resolve(jsonResponse({ ...analysisResult, request_id: 'predict-456', current_prediction: { ni_recovery_pct: 88.8, co_recovery_pct: 79.5 },
          recommendation: { ...analysisResult.recommendation, process_conditions: { ...analysisResult.recommendation.process_conditions, sulfuric_acid_l: 1400 } } }))
      }
      if (String(url).endsWith('/factory/apply')) applied = JSON.parse(String(init?.body))
      return defaultFetch(url, init)
    }))
    render(<App />)
    await prepare()
    change('황산 투입량 (L)', '1200')
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '추천값 적용하기' })).toBeEnabled()
    await predict()
    expect(body).toMatchObject({ current_process: { feed_amount_kg: 1000, sulfuric_acid_l: 1200, leaching_temperature_c: 62, leaching_time_hr: 5.5 } })
    expect(screen.getByRole('group', { name: '입력 조건 예상 회수율' })).toHaveTextContent('88.8%')
    expect(within(screen.getByLabelText('추천 공정 조건')).getByText('1050')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: '가상 공장에 적용' }))
    await screen.findByText('명령 대기 중')
    expect(applied).toMatchObject({ analysis_request_id: 'predict-456', process_conditions: { sulfuric_acid_l: 1200 },
      material: { name: '혼합 원료 A', feed_amount_kg: 1000, ni_content_pct: 12.17 },
      expected_recovery: { ni_recovery_pct: 88.8, co_recovery_pct: 79.5 } })
  })
  it.each([['원료 이름', '새 원료'], ['철 불순물 (%)', '3'], ['원료 투입량 (kg)', '800']])('invalidates recommendation and prediction when %s changes', async (label, value) => {
    vi.stubGlobal('fetch', vi.fn(defaultFetch))
    render(<App />)
    await prepare()
    change(label, value)
    expect(screen.getByRole('button', { name: '추천값 적용하기' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
    expect(screen.getByText('원료 변경 · 다시 추천 필요')).toBeInTheDocument()
    await recommend()
    expect(screen.getByRole('button', { name: '추천값 적용하기' })).toBeEnabled()
  })
  it('rejects stale recommendation responses after a material edit during the request', async () => {
    let resolve!: (response: Response) => void
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/process/analyze')) return new Promise<Response>((done) => { resolve = done })
      return defaultFetch(url, init)
    }))
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: '최적 공정 추천' }))
    change('니켈 함량 (%)', '20')
    await act(async () => { resolve(jsonResponse(analysisResult)) })
    expect(screen.getByRole('button', { name: '추천값 적용하기' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
  })
  it('does not apply a prediction response if the process changed while it was pending', async () => {
    let attempt = 0
    let resolve!: (response: Response) => void
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/process/analyze') && ++attempt === 2) return new Promise<Response>((done) => { resolve = done })
      return defaultFetch(url, init)
    }))
    render(<App />)
    await prepare()
    change('황산 투입량 (L)', '1200')
    fireEvent.click(screen.getByRole('button', { name: '회수율 예측' }))
    change('황산 투입량 (L)', '1300')
    await act(async () => { resolve(jsonResponse(analysisResult)) })
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
    expect(screen.getByRole('group', { name: '입력 조건 예상 회수율' })).not.toHaveTextContent('85.65%')
  })
  it('preserves the recommendation after a failed prediction and allows retry', async () => {
    let attempt = 0
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/process/analyze') && ++attempt === 2) return Promise.resolve(jsonResponse({ error: { message: '예측 실패', details: [{ field: 'material.ni_content_pct', message: '입력값을 확인해 주세요.' }] } }, 502))
      return defaultFetch(url, init)
    }))
    render(<App />)
    await prepare()
    change('황산 투입량 (L)', '1200')
    await predict()
    expect(screen.getByRole('alert')).toHaveTextContent('입력값을 확인해 주세요.')
    expect(within(screen.getByLabelText('추천 공정 조건')).getByText('1050')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
    await predict()
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeEnabled()
  })
  it('keeps the last recommendation after a material validation failure but prevents using it', async () => {
    let attempt = 0
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/process/analyze') && ++attempt === 2) return Promise.resolve(jsonResponse({
        error: { message: '입력값을 확인해 주세요.', details: [{ field: 'material.ni_content_pct', message: '니켈 함량은 0~100 범위여야 합니다.' }] },
      }, 422))
      return defaultFetch(url, init)
    }))
    render(<App />)
    await prepare()
    change('니켈 함량 (%)', '101')
    await recommend()
    const issue = screen.getByRole('button', { name: '니켈 함량 (%) 오류' })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    fireEvent.mouseEnter(issue)
    expect(screen.getByRole('tooltip')).toHaveTextContent('니켈 함량은 0~100 범위여야 합니다.')
    expect(within(screen.getByLabelText('추천 공정 조건')).getByText('1050')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '추천값 적용하기' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
  })
  it('marks invalid A numeric inputs before submitting and clears each mark on correction', async () => {
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/system/status')) return Promise.resolve(jsonResponse({
        backend: 'ok', a_adapter: 'live', a_ready: true, c_adapter: 'mock',
      }))
      return defaultFetch(url, init)
    }))
    render(<App />)
    await screen.findByText('A 연결')
    change('니켈 함량 (%)', '7.9')
    change('황산 투입량 (L)', '1600')
    const ni = screen.getByRole('button', { name: '니켈 함량 (%) 오류' })
    const acid = screen.getByRole('button', { name: '황산 투입량 (L) 오류' })
    expect(screen.getByLabelText('니켈 함량 (%)')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    fireEvent.focus(acid)
    expect(screen.getByRole('tooltip')).toHaveTextContent('400~1500 L')
    fireEvent.keyDown(acid, { key: 'Escape' })
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    fireEvent.click(ni)
    expect(screen.getByRole('tooltip')).toHaveTextContent('8~30%')
    change('니켈 함량 (%)', '8')
    expect(ni).not.toBeInTheDocument()
    expect(acid).toBeInTheDocument()
    change('황산 투입량 (L)', '1500')
    expect(acid).not.toBeInTheDocument()
  })
  it('can predict a manually entered process before requesting a recommendation', async () => {
    vi.stubGlobal('fetch', vi.fn(defaultFetch))
    render(<App />)
    await screen.findByText('B 연결')
    change('황산 투입량 (L)', '900')
    change('침출 온도 (°C)', '60')
    change('침출 시간 (시간)', '4')
    await predict()
    expect(screen.getByRole('group', { name: '입력 조건 예상 회수율' })).toHaveTextContent('85.65%')
    expect(screen.getByRole('button', { name: '추천값 적용하기' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeEnabled()
  })
  it('prevents duplicate apply while pending and allows retry after failure', async () => {
    let attempts = 0
    let resolve!: (response: Response) => void
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/factory/apply') && ++attempts === 1) return new Promise<Response>((done) => { resolve = done })
      return defaultFetch(url, init)
    }))
    render(<App />)
    await prepare()
    const button = screen.getByRole('button', { name: '가상 공장에 적용' })
    fireEvent.click(button)
    fireEvent.click(button)
    expect(attempts).toBe(1)
    expect(screen.getByRole('button', { name: '새 작업 시작' })).toBeDisabled()
    expect(screen.getByLabelText('니켈 함량 (%)')).toBeDisabled()
    await act(async () => { resolve(jsonResponse({ error: { message: '명령 등록 실패' } }, 503)) })
    expect(screen.getByRole('alert')).toHaveTextContent('명령 등록 실패')
    fireEvent.click(screen.getByRole('button', { name: '가상 공장에 적용' }))
    await screen.findByText('명령 대기 중')
    expect(attempts).toBe(2)
  })
  it.each(['queued', 'running'])('keeps polling repeated %s states until completion', async (phase) => {
    vi.useFakeTimers()
    let reads = 0
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/factory/state')) return Promise.resolve(jsonResponse({ ...running, state: ++reads < 4 ? phase : 'completed', progress_pct: reads < 4 ? 35 : 100 }))
      return defaultFetch(url, init)
    }))
    render(<App />)
    for (let i = 0; i < 5; i++) await act(async () => { await vi.advanceTimersByTimeAsync(1000) })
    expect(screen.getByText('완료')).toBeInTheDocument()
  })
  it('recovers connections after temporary failure', async () => {
    vi.useFakeTimers()
    let offline = true
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => offline ? Promise.reject(new Error('offline')) : defaultFetch(url, init)))
    render(<App />)
    await act(async () => { await vi.advanceTimersByTimeAsync(0) })
    expect(screen.getByLabelText('연동 상태').textContent).toBe('A 미연결B 미연결C 미연결')
    offline = false
    await act(async () => { await vi.advanceTimersByTimeAsync(2000) })
    expect(screen.getByText('B 연결')).toBeInTheDocument()
  })
  it.each(['running', 'error'])('keeps the Unity %s state visible during recommendation', async (state) => {
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/factory/state')) return Promise.resolve(jsonResponse({ ...running, state }))
      return defaultFetch(url, init)
    }))
    render(<App />)
    await prepare()
    expect(screen.getByText(state === 'running' ? '실행 중 · 35%' : '오류')).toBeInTheDocument()
    if (state === 'running') expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
    else expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeEnabled()
  })
})
