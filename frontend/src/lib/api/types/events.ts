export type EventRegion = "pushkin_gory" | "pskov";

export interface PublicEvent {
  id: number;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string | null;
  starts_at_label: string;
  ends_at_label: string | null;
  location: string | null;
  region: EventRegion;
  region_label: string;
  category: string;
  category_label: string;
  genre: string | null;
  poster_url: string | null;
  source: string | null;
  source_url: string | null;
}

export interface PublicEventListResponse {
  items: PublicEvent[];
  total: number;
}

export interface EventItem {
  id: number;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string | null;
  starts_at_label: string;
  ends_at_label: string | null;
  location: string | null;
  region: EventRegion;
  region_label: string;
  category: string;
  category_label: string;
  genre: string | null;
  poster_url: string | null;
  source: string | null;
  source_url: string | null;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface EventCreate {
  title: string;
  description?: string;
  starts_at: string;
  ends_at?: string | null;
  location?: string;
  region?: EventRegion;
  category: string;
  source?: string;
  source_url?: string;
  is_published?: boolean;
}

export interface EventListResponse {
  items: EventItem[];
  total: number;
}

export interface EventSyncResult {
  source: string;
  region: string;
  fetched: number;
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
}

export type EventSourceHealth = "ready" | "group_token_only" | "needs_token";

export interface EventSourceOverviewItem {
  id: string;
  label: string;
  health: EventSourceHealth;
  published_count: number;
  token_hint: string | null;
  last_synced_at: string | null;
}

export interface EventSourcesOverview {
  sources: EventSourceOverviewItem[];
  total_published: number;
  event_sources_health: Record<string, EventSourceHealth>;
}
