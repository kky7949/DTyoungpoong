import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from '../../App'

const systemStatus = {
  backend: 'ok',
  a_adapter: 'mock',
  c_adapter: 'mock',
  capabilities: {
    prediction: true,
    optimization: true,
    xai: false,
    unity_control: true,
  },
}

const analysisResult = {
  schema_version: 'draft-1',
  source: 'mock',
  generated_at: '2026-10-14T21:00:00+09:00',
  request_id: 'analysis-123',
  current_prediction: {
    ni_recovery_pct: 85.65,
    co_recovery_pct: 78.45,
  },
  recommendation: {
    process_conditions: {
      sulfuric_acid_l: 1050,
      leaching_temperature_c: 62,
      leaching_time_hr: 5.5,
    },
    expected_recovery: {
      ni_recovery_pct: 89.2,
      co_recovery_pct: 82.1,
    },
  },
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function defaultFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = String(input)
  if (url.endsWith('/health')) return Promise.resolve(jsonResponse({ status: 'ok' }))
  if (url.endsWith('/api/v1/system/status')) return Promise.resolve(jsonResponse(systemStatus))
  if (url.endsWith('/api/v1/process/analyze')) {
    return Promise.resolve(jsonResponse(analysisResult))
  }
  if (url.endsWith('/api/v1/factory/apply')) {
    return Promise.resolve(
      jsonResponse({ command_id: 'command-123', status: 'queued', source: 'mock' }, 202),
    )
  }
  if (url.endsWith('/api/v1/factory/state')) {
    return Promise.resolve(
      jsonResponse({
        source: 'mock',
        state: 'running',
        command_id: 'command-123',
        progress_pct: 35,
        message: 'Mock Unity process running',
        updated_at: '2026-10-14T21:00:01+09:00',
      }),
    )
  }
  return Promise.reject(new Error(`Unexpected request: ${url} ${init?.method ?? 'GET'}`))
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

describe('HMI dashboard', () => {
  it('shows B availability and clearly labels A/C mock adapters', async () => {
    vi.stubGlobal('fetch', vi.fn(defaultFetch))

    render(<App />)

    expect(await screen.findByText('B 서버 정상')).toBeInTheDocument()
    expect(screen.getByText('A 모의 데이터')).toBeInTheDocument()
    expect(screen.getByText('C 모의 데이터')).toBeInTheDocument()
    expect(screen.getByText('XAI 미지원')).toBeInTheDocument()
  })

  it('distinguishes a connection failure from mock status', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('offline'))))

    render(<App />)

    expect(await screen.findByText('B 서버에 연결할 수 없습니다.')).toBeInTheDocument()
    expect(screen.queryByText('B 서버 정상')).not.toBeInTheDocument()
  })

  it('sends blank numeric input as null and renders Korean mock results', async () => {
    let analysisBody: unknown
    let resolveAnalysis: ((response: Response) => void) | undefined
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith('/api/v1/process/analyze')) {
        analysisBody = JSON.parse(String(init?.body))
        return new Promise<Response>((resolve) => {
          resolveAnalysis = resolve
        })
      }
      return defaultFetch(input, init)
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('B 서버 정상')

    fireEvent.change(screen.getByLabelText('니켈 함량 (%)'), { target: { value: '' } })
    await user.click(screen.getByRole('button', { name: '예측 및 최적화 실행' }))

    expect(screen.getByRole('button', { name: '분석 중...' })).toBeDisabled()
    expect(analysisBody).toMatchObject({ material: { ni_content_pct: null } })

    await act(async () => {
      resolveAnalysis?.(jsonResponse(analysisResult))
    })

    expect(await screen.findByText('모의 데이터')).toBeInTheDocument()
    expect(screen.getByText('Ni 85.65%')).toBeInTheDocument()
    expect(screen.getByText('Co 78.45%')).toBeInTheDocument()
    expect(screen.getByText('추천 침출 온도 62°C')).toBeInTheDocument()
    expect(screen.getByText('일부 결측값은 AI 전처리 과정에서 보정됩니다.')).toBeInTheDocument()
  })

  it('keeps the last successful result when a later analysis is rejected', async () => {
    let analysisCount = 0
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input).endsWith('/api/v1/process/analyze')) {
          analysisCount += 1
          if (analysisCount === 1) return Promise.resolve(jsonResponse(analysisResult))
          return Promise.resolve(
            jsonResponse(
              {
                error: {
                  code: 'VALIDATION_ERROR',
                  message: '입력값을 확인해 주세요.',
                  details: [],
                },
                request_id: 'error-123',
              },
              422,
            ),
          )
        }
        return defaultFetch(input, init)
      }),
    )
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('B 서버 정상')

    await user.click(screen.getByRole('button', { name: '예측 및 최적화 실행' }))
    expect(await screen.findByText('Ni 85.65%')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '예측 및 최적화 실행' }))

    expect(await screen.findByText('입력값을 확인해 주세요.')).toBeInTheDocument()
    expect(screen.getByText('Ni 85.65%')).toBeInTheDocument()
  })

  it('enables factory apply only after analysis and refreshes running state', async () => {
    vi.stubGlobal('fetch', vi.fn(defaultFetch))
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('B 서버 정상')

    expect(screen.getByRole('button', { name: '가상 공장에 적용' })).toBeDisabled()
    await user.click(screen.getByRole('button', { name: '예측 및 최적화 실행' }))
    await screen.findByText('Ni 85.65%')
    await user.click(screen.getByRole('button', { name: '가상 공장에 적용' }))

    expect(await screen.findByText('명령 대기 중')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('실행 중 · 35%')).toBeInTheDocument())
  })
})
