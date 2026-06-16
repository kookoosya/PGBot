export interface User {
  id: number;
  username: string;
  email: string | null;
  full_name: string | null;
  phone?: string | null;
  role: string;
  department_id: number | null;
  is_active: boolean;
  organization?: string | null;
  position?: string | null;
  verification_status?: string | null;
  created_at: string;
}

export interface Issue {
  id: number;
  title: string | null;
  description: string;
  status: string;
  category: string | null;
  priority: string;
  address: string | null;
  resident_id: number | null;
  department_id: number | null;
  assignee_id: number | null;
  confirmation_count: number;
  is_spam: boolean;
  resolution_text: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
  photos: { id: number; url: string }[];
  ai_analysis: {
    is_valid: boolean;
    category: string | null;
    priority: string | null;
    summary: string | null;
    duplicate_probability: number | null;
    suggested_department: string | null;
  } | null;
  status_timeline?: IssueStatusEvent[];
}

export interface IssueStatusEvent {
  status: string;
  label: string;
  at: string;
  previous_status: string | null;
  resolution?: string | null;
}

export interface IssueMyListResponse {
  items: Issue[];
  total: number;
  page: number;
  page_size: number;
}

export interface IssueListResponse {
  items: Issue[];
  total: number;
  page: number;
  page_size: number;
}

export interface Department {
  id: number;
  name: string;
  description: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  is_active: boolean;
}

export interface Statistics {
  total_issues: number;
  resolved_issues: number;
  in_progress_issues: number;
  rejected_issues: number;
  avg_resolution_hours: number | null;
  top_categories: { category: string; count: number }[];
  top_streets: { street: string; count: number }[];
  monthly_dynamics: { month: string; count: number; resolved: number }[];
}

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

export interface AuditLog {
  id: number;
  user: string | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface Notification {
  id: number;
  issue_id: number | null;
  channel: string;
  priority: string;
  status: string;
  message: string;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatResponse {
  reply: string;
  remaining: number;
  daily_limit: number;
  limit_reached: boolean;
  model?: string;
}

export interface AIModelOption {
  id: string;
  label: string;
  provider: string;
  desc?: string;
  fast?: boolean;
  smart?: boolean;
}

export interface AIStatus {
  ready: boolean;
  chat_provider: string;
  image_provider: string;
  pollinations_configured: boolean;
  openrouter_configured?: boolean;
  gemini_configured: boolean;
  providers?: string[];
  message: string;
  limits?: {
    site_daily: number;
    site_note: string;
    providers_note: string;
  };
}

export interface AIModelsInfo {
  chat_models: AIModelOption[];
  image_models: AIModelOption[];
  capabilities: string[];
  status?: AIStatus;
}

export interface ImageGenResult {
  url: string | null;
  model: string;
  prompt: string;
  provider?: string;
  error?: string;
}

export interface UsageInfo {
  used: number;
  remaining: number;
  daily_limit: number;
  payment_info?: PaymentInfo;
}

export interface ClassifiedMarketingStats {
  total_ads: number;
  total_views: number;
  avg_views_per_ad: number;
  monthly_reach_estimate: number;
  placement_fee: number;
  period_days: number;
  category_stats: { category: string; label: string; ads: number; views: number }[];
  roi_examples: {
    service: string;
    ad_cost: number;
    clients: number;
    avg_check: number;
    income: number;
    roi_percent: number;
  }[];
  weekly_views: { day: string; views: number }[];
}

export interface PaymentInfo {
  card_number: string;
  card_holder?: string;
  bank_name?: string;
  amount_suggested: number;
  message: string;
}

export interface Place {
  id: number;
  name: string;
  category: string;
  category_label: string;
  description: string | null;
  address: string | null;
  latitude: number;
  longitude: number;
  phone: string | null;
  website: string | null;
  opening_hours: string | null;
  avg_rating: number;
  review_count: number;
  external_rating: number;
  external_review_count: number;
  display_rating: number;
  display_review_count: number;
  rating_source: string | null;
  yandex_url: string | null;
  complaint_count: number;
}

export interface CatalogItem {
  id: number;
  name: string;
  category: string;
  category_label: string;
  description: string | null;
  phone: string | null;
  external_url: string | null;
  price_hint: string | null;
  address: string | null;
  source: string;
  is_internal: boolean;
  sort_order: number;
}

export interface CatalogItemAdmin extends CatalogItem {
  is_active: boolean;
  seed_key: string | null;
  created_at: string;
}

export interface CatalogItemCreate {
  name: string;
  category: string;
  description?: string;
  phone?: string;
  external_url?: string;
  price_hint?: string;
  address?: string;
  is_internal?: boolean;
  sort_order?: number;
}

export interface TaxiService {
  id: number;
  name: string;
  phone: string;
  phones_extra: string | null;
  description: string | null;
  is_24h: boolean;
  rating: number;
  price_from: number | null;
}

export interface PlaceDetail extends Place {
  reviews: { id: number; rating: number; text: string | null; author_name: string | null; created_at: string }[];
  recent_complaints: { id: number; complaint_type: string; complaint_label: string; description: string; price_tagged: string | null; price_charged: string | null; status: string; created_at: string }[];
}

export interface PlaceListResponse {
  items: Place[];
  total: number;
}

export interface MapStats {
  total_places: number;
  by_category: Record<string, number>;
  last_sync: string | null;
  center: { lat: number; lng: number };
}

export interface ServiceProvider {
  id: number;
  full_name: string;
  phone: string;
  bio: string | null;
  address: string | null;
  avg_rating: number;
  review_count: number;
  services: { id: number; name: string; service_type: string; service_label: string; duration_minutes: number; price: number | null }[];
  status_today: string;
  next_free_slot: string | null;
}

export interface TimeSlot {
  time: string;
  available: boolean;
  label: string;
}

export interface SlotsResult {
  date: string;
  working_hours: string | null;
  slots: TimeSlot[];
}

export interface ProviderDetail extends ServiceProvider {
  schedule: { day_of_week: number; day_label: string; start_time: string; end_time: string; is_working: boolean }[];
  verification_status: string;
}

export interface AppointmentItem {
  id: number;
  provider_name: string;
  service_name: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  status: string;
  client_name: string;
}

export interface BusyBlock {
  id: number;
  block_date: string;
  start_time: string;
  end_time: string;
  reason: string | null;
}

export interface ClassifiedPaymentInfo {
  card_number: string;
  amount: number;
  period_days: number;
  message: string;
  free_limit: number;
  free_used: number;
  free_remaining: number;
  requires_payment: boolean;
}

export interface ClassifiedAd {
  id: number;
  category: string;
  category_label: string;
  title: string;
  description: string;
  price: number | null;
  price_unit: string | null;
  phone: string;
  author_name: string;
  address: string | null;
  created_at: string;
}

export interface ClassifiedMineAd extends ClassifiedAd {
  payment_status: string;
  is_active: boolean;
}

export interface ClassifiedPending extends ClassifiedAd {
  payment_status: string;
  payment_reference: string | null;
  placement_fee: number;
  contact_vk?: string | null;
}

export interface PendingProvider {
  id: number;
  full_name: string;
  phone: string;
  address: string | null;
  services: string[];
}

export interface ComplaintType {
  value: string;
  label: string;
}

export interface MapRouteStop {
  name: string;
  address: string;
  latitude: number;
  longitude: number;
}

export interface MapRoute {
  id: string;
  title: string;
  duration: string;
  description: string;
  stops: MapRouteStop[];
}

export interface MapFilterMode {
  id: string;
  label: string;
  category: string | null;
  shops_only: boolean;
  useful_only: boolean;
  show_taxi: boolean;
}

export interface FeedbackItem {
  id: number;
  message: string;
  contact: string | null;
  page: string | null;
  status: string;
  created_at: string;
}

export interface VerificationRequest {
  id: number;
  username: string;
  email: string | null;
  full_name: string | null;
  phone: string | null;
  organization: string | null;
  position: string | null;
  role: string;
  verification_status: string;
  verification_note: string | null;
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

export interface VkModerationState {
  vk_user_id: number;
  peer_id: number;
  warning_count: number;
  banned_until: string | null;
  last_violation_at: string | null;
  updated_at: string;
}

export interface VkModerationLog {
  id: number;
  vk_user_id: number;
  peer_id: number;
  message_excerpt: string;
  reason: string;
  action: string;
  warning_number: number;
  created_at: string;
}

export interface VkModerationOverview {
  states: VkModerationState[];
  recent_logs: VkModerationLog[];
}

export interface EventSyncResult {
  region: string;
  fetched: number;
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
}
