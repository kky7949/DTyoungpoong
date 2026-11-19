export type AdapterMode = 'mock' | 'live'
export type RecommendationMode = 'joint' | 'ni' | 'co'

export interface SystemStatus {
  backend: string
  a_adapter: AdapterMode
  a_ready?: boolean
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
    name: string | null
    ni_content_pct: number | null
    co_content_pct: number | null
    li_content_pct: number | null
    mn_content_pct: number | null
    cu_content_pct: number | null
    fe_content_pct: number | null
    al_content_pct: number | null
  }
  current_process: {
    feed_amount_kg: number | null
    sulfuric_acid_l: number | null
    leaching_temperature_c: number | null
    leaching_time_hr: number | null
  }
  options?: { mode: RecommendationMode }
}

export interface ProcessConditions {
  sulfuric_acid_l: number
  leaching_temperature_c: number
  leaching_time_hr: number
}

export interface RecoveryPrediction {
  ni_recovery_pct: number
  co_recovery_pct: number
}

export interface Recommendation {
  process_conditions: ProcessConditions
  expected_recovery: RecoveryPrediction
}

export interface AnalysisResult {
  schema_version: string
  source: AdapterMode
  generated_at: string
  request_id: string
  material_grade?: string | null
  current_prediction: RecoveryPrediction | null
  recommendation: Recommendation | null
  model_version?: string | null
  status?: string | null
  mode?: RecommendationMode | null
  warnings?: string[]
  closest_alternative?: Recommendation | null
}

export interface ApplyFactoryResult {
  command_id: string
  status: 'queued'
  source: AdapterMode
}

export interface ApplyFactoryRequest {
  analysis_request_id: string
  material: AnalyzeRequest['material'] & { feed_amount_kg: number | null }
  process_conditions: ProcessConditions
  expected_recovery: RecoveryPrediction
}

export interface FactoryState {
  source: AdapterMode
  state: 'disconnected' | 'idle' | 'queued' | 'running' | 'completed' | 'error'
  command_id: string | null
  progress_pct: number
  message: string
  updated_at: string
  connection_status: 'connected' | 'disconnected'
  last_seen_at: string | null
}

export interface ApiErrorBody {
  error?: { message?: string; details?: Array<{ field: string; message: string }> }
}
