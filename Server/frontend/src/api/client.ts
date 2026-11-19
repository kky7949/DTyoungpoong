import type {
  AnalysisResult,
  AnalyzeRequest,
  ApiErrorBody,
  ApplyFactoryResult,
  ApplyFactoryRequest,
  FactoryState,
  SystemStatus,
} from './types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export class ApiRequestError extends Error {
  readonly status: number
  readonly summary: string
  readonly details: NonNullable<NonNullable<ApiErrorBody['error']>['details']>

  constructor(
    status: number,
    summary: string,
    details: ApiRequestError['details'],
  ) {
    super([summary, ...details.map((detail) => detail.message)].join(' '))
    this.status = status
    this.summary = summary
    this.details = details
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    signal: init?.signal ?? AbortSignal.timeout(5000),
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let message = `요청에 실패했습니다. (${response.status})`
    let details: ApiRequestError['details'] = []
    try {
      const body = (await response.json()) as ApiErrorBody
      message = body.error?.message ?? message
      if (Array.isArray(body.error?.details)) {
        details = body.error.details.filter((detail) => detail &&
          typeof detail.field === 'string' && typeof detail.message === 'string' && detail.message)
      }
    } catch {
      // JSON이 아닌 오류 응답은 상태 코드 기반 메시지를 사용한다.
    }
    throw new ApiRequestError(response.status, message, details)
  }

  return response.json() as Promise<T>
}

export async function getSystemStatus(): Promise<SystemStatus> {
  await requestJson<{ status: string }>('/health')
  return requestJson<SystemStatus>('/api/v1/system/status')
}

export function analyzeProcess(payload: AnalyzeRequest): Promise<AnalysisResult> {
  return requestJson<AnalysisResult>('/api/v1/process/analyze', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function applyFactory(payload: ApplyFactoryRequest): Promise<ApplyFactoryResult> {
  return requestJson<ApplyFactoryResult>('/api/v1/factory/apply', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getFactoryState(): Promise<FactoryState> {
  return requestJson<FactoryState>('/api/v1/factory/state')
}
