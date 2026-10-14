import type {
  AnalysisResult,
  AnalyzeRequest,
  ApiErrorBody,
  ApplyFactoryResult,
  FactoryState,
  ProcessConditions,
  SystemStatus,
} from './types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let message = `요청에 실패했습니다. (${response.status})`
    try {
      const body = (await response.json()) as ApiErrorBody
      message = body.error?.message ?? message
    } catch {
      // JSON이 아닌 오류 응답은 상태 코드 기반 메시지를 사용한다.
    }
    throw new Error(message)
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

export function applyFactory(
  analysisRequestId: string,
  processConditions: ProcessConditions,
): Promise<ApplyFactoryResult> {
  return requestJson<ApplyFactoryResult>('/api/v1/factory/apply', {
    method: 'POST',
    body: JSON.stringify({
      analysis_request_id: analysisRequestId,
      process_conditions: processConditions,
    }),
  })
}

export function getFactoryState(): Promise<FactoryState> {
  return requestJson<FactoryState>('/api/v1/factory/state')
}
