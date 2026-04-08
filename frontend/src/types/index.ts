export interface MediaItem {
  id: string;
  file_path: string;
  thumbnail_path: string | null;
  mime_type: string | null;
  width: number | null;
  height: number | null;
}

export interface TagItem {
  id: string;
  name: string;
  source: string;
}

export interface TimelineEvent {
  id: string;
  source: string;
  source_id: string | null;
  event_type: string;
  title: string | null;
  body: string | null;
  occurred_at: string;
  occurred_at_precision: string;
  location_lat: number | null;
  location_lng: number | null;
  location_name: string | null;
  created_at: string;
  media: MediaItem[];
  tags: TagItem[];
}

export interface EventListResponse {
  items: TimelineEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface SearchResponse {
  items: TimelineEvent[];
  total: number;
  mode: 'fts' | 'semantic' | 'hybrid';
  query: string;
}

export interface ImportJob {
  id: string;
  source: string;
  status: 'pending' | 'running' | 'done' | 'failed';
  original_filename: string | null;
  total_events: number;
  imported_events: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface ParserInfo {
  source_name: string;
  display_name: string;
  description: string;
  supported_extensions: string[];
}

export interface HealthStatus {
  status: string;
  ai_backend: string;
  ai_available: boolean;
}

export interface SourceCount {
  source: string;
  count: number;
}

export interface DateRange {
  min: string | null;
  max: string | null;
}
