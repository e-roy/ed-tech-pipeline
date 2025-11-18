export enum SessionStage {
  CREATED = "created",
  IMAGE_GENERATION = "image_generation",
  IMAGE_SELECTION = "image_selection",
  CLIP_GENERATION = "clip_generation",
  CLIP_SELECTION = "clip_selection",
  FINAL_COMPOSITION = "final_composition",
  COMPLETE = "complete",
  FAILED = "failed",
}

export interface ImageAsset {
  id: string;
  url: string;
  view_type: string;
  seed: number;
  cost: number;
  created_at: string;
}

export interface VideoAsset {
  id: string;
  url: string;
  source_image_id: string;
  duration: number;
  resolution: string;
  fps: number;
  cost: number;
  created_at: string;
}

export interface FinalVideo {
  url: string;
  duration: number;
  resolution: string;
  fps: number;
  file_size_mb: number;
  format: string;
}

export interface Session {
  id: string;
  user_id: number;
  stage: SessionStage;
  product_prompt?: string;
  video_prompt?: string;
  consistency_seed?: number;
  generated_images: ImageAsset[];
  approved_images: string[];
  generated_clips: VideoAsset[];
  approved_clips: string[];
  final_video?: FinalVideo;
  total_cost: number;
  created_at: string;
  updated_at: string;
}

export interface ProgressUpdate {
  session_id: string;
  stage: string;
  progress: number;
  message: string;
  current_cost?: number;
  timestamp: string;
  data?: unknown;
  error?: string;
  video_url?: string;
}

export interface TextOverlay {
  product_name: string;
  cta: string;
  font: string;
  color: string;
}

export interface AudioConfig {
  enabled: boolean;
  genre: string;
}

export interface Fact {
  concept: string;
  details: string;
  confidence: number;
}
