import type { EventRegion } from "./events";

export interface PublicInfo {
  site_url: string;
  vk_url: string;
  vk_bot_ready?: boolean;
  vk_mini_app_ready?: boolean;
  vk_app_id?: string | null;
  vk_bot_hint?: string;
  map_url: string;
  yandex_maps_add_org: string;
  portal_links?: {
    home: string;
    complaints: string;
    complaints_new: string;
    classifieds: string;
    classifieds_new: string;
    events: string;
    cabinet: string;
    map: string;
    jobs: string;
  };
}

export interface VisitStats {
  today: number;
  week: number;
  month: number;
  total: number;
  unique_today: number;
  unique_week: number;
  top_pages: { path: string; label: string; count: number }[];
  daily: { day: string; visits: number; unique_visitors: number }[];
}

export interface FeedbackItem {
  id: number;
  message: string;
  contact: string | null;
  page: string | null;
  status: string;
  created_at: string;
}

export interface WeatherCurrent {
  temperature: number;
  apparent_temperature: number;
  humidity: number;
  precipitation: number;
  wind_speed: number;
  weather_code: number;
  description: string;
  icon: string;
  time: string;
}

export interface WeatherHourlyItem {
  time: string;
  hour_label: string;
  temperature: number;
  apparent_temperature: number;
  precipitation: number;
  precipitation_probability: number | null;
  humidity: number | null;
  wind_speed: number;
  weather_code: number;
  description: string;
  icon: string;
}

export interface WeatherResponse {
  location_name: string;
  latitude: number;
  longitude: number;
  timezone: string;
  updated_at: string;
  current: WeatherCurrent;
  hourly: WeatherHourlyItem[];
  cache_ttl_seconds: number;
}

export interface TodayClassifiedSnippet {
  id: number;
  title: string;
  category_label: string;
  created_at: string;
}

export interface TodayMapSnippet {
  total_places: number;
  total_reviews: number;
  active_taxi_count: number;
  route_count: number;
}

export interface TodayEventSnippet {
  id: number;
  title: string;
  starts_at: string;
  starts_at_label: string;
  ends_at_label?: string | null;
  location?: string | null;
  region: EventRegion;
  region_label: string;
  category: string;
  category_label: string;
  genre?: string | null;
  poster_url?: string | null;
  description?: string | null;
  source?: string | null;
  source_url?: string | null;
}

export interface TodayResponse {
  weather: WeatherResponse | null;
  latest_classified: TodayClassifiedSnippet | null;
  map: TodayMapSnippet;
  upcoming_events: TodayEventSnippet[];
  updated_at: string;
  cache_ttl_seconds: number;
}

export type { EventRegion };
