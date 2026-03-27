export type SourceType = "prompt" | "document" | "lesson_request";
export type ProjectStatus = "draft" | "active" | "completed" | "failed";
export type VisualStyle =
  | "clean_academic"
  | "modern_infographic"
  | "cinematic_technical"
  | "playful_educational"
  | "startup_explainer";
export type JobType = "full_render" | "preview";
export type JobStatus =
  | "pending"
  | "planning"
  | "queued"
  | "running"
  | "composing"
  | "completed"
  | "failed"
  | "canceled";
export type SceneStatus = "pending" | "ready" | "rendering" | "completed" | "failed" | "skipped";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  picture_url: string | null;
  provider: string;
  created_at: string;
  updated_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthSession {
  user: User;
  tokens: TokenPair;
}

export interface AuthUrlResponse {
  authorization_url: string;
  state: string;
}

export interface Project {
  id: string;
  user_id: string;
  title: string;
  prompt: string;
  source_type: SourceType;
  source_document_path: string | null;
  requested_duration_minutes: number;
  visual_style: VisualStyle;
  topic_domain: string | null;
  status: ProjectStatus;
  scene_plan_version: number;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreatePayload {
  title: string;
  prompt: string;
  source_type: SourceType;
  requested_duration_minutes: number;
  visual_style: VisualStyle;
  topic_domain?: string;
  metadata_json?: Record<string, unknown>;
}

export interface Job {
  id: string;
  project_id: string;
  job_type: JobType;
  status: JobStatus;
  target_resolution: string;
  requested_duration_seconds: number;
  llm_provider: string;
  tts_provider: string;
  image_generation_enabled: boolean;
  progress_pct: number;
  render_plan_json: Record<string, unknown>;
  current_step: string | null;
  retry_count: number;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobCreatePayload {
  job_type: JobType;
  requested_duration_minutes?: number;
  diagnostics_mode?: boolean;
  image_generation_enabled?: boolean;
  llm_provider?: string;
  tts_provider?: string;
  preview_only?: boolean;
}

export interface Scene {
  id: string;
  project_id: string;
  job_id: string;
  order_index: number;
  title: string;
  scene_type: string;
  learning_objective: string;
  narration_text: string;
  estimated_duration_seconds: number;
  renderer_key: string;
  spec_json: Record<string, unknown>;
  status: SceneStatus;
  output_file_id: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobLog {
  id: string;
  level: string;
  event: string;
  message: string;
  payload_json: Record<string, unknown>;
  created_at: string;
}

export interface VideoSpecScene {
  scene_id: string;
  order_index: number;
  title: string;
  scene_type: string;
  learning_objective: string;
  estimated_duration_seconds: number;
  visual_style: VisualStyle;
  renderer_key: string;
  equations: string[];
}

export interface VideoSpec {
  title: string;
  objective: string;
  topic_domain: string;
  complexity_score: number;
  target_duration_seconds: number;
  estimated_total_duration_seconds: number;
  scene_count: number;
  style: VisualStyle;
  llm_provider: string;
  scenes: VideoSpecScene[];
}

export interface JobStatusResponse {
  job: Job;
  scenes: Scene[];
  video_spec: VideoSpec | null;
}

export interface GoogleCallbackPayload {
  code: string;
  state: string;
}
