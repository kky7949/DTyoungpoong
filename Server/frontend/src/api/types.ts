export type AdapterMode = 'mock' | 'live'

export interface SystemStatus {
  backend: string
  a_adapter: AdapterMode
  c_adapter: AdapterMode
  capabilities: {
    prediction: boolean
    optimization: boolean
    xai: boolean
    unity_control: boolean
  }
}

export interface AnalyzeRequest {
  material: {
    grade: string | null
    ni_content_pct: number | null
    co_content_pct: number | null
  }
  current_process: {
    feed_amount_kg: number | null
    sulfuric_acid_l: number | null
    leaching_temperature_c: number | null
    leaching_time_hr: number | null
  }
}

export interface ProcessConditions {
  sulfuric_acid_l: number
  leaching_temperature_c: number
  leaching_time_hr: number
}

export interface AnalysisResult {
  schema_version: string
  source: AdapterMode
  generated_at: string
  request_id: string
  current_prediction: {
    ni_recovery_pct: number
    co_recovery_pct: number
  }
  recommendation: {
    process_conditions: ProcessConditions
    expected_recovery: {
      ni_recovery_pct: number
      co_recovery_pct: number
    }
  }
}

export interface ApplyFactoryResult {
  command_id: string
  status: 'queued'
  source: AdapterMode
}

export interface FactoryState {
  source: AdapterMode
  state: 'disconnected' | 'idle' | 'queued' | 'running' | 'completed' | 'error'
  command_id: string | null
  progress_pct: number
  message: string
  updated_at: string
}

export interface ApiErrorBody {
  error?: { message?: string }
}
