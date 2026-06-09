/** Shared API response types grouped by domain. */

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
  vk_bot_hint?: string;
  map_url: string;
  yandex_maps_add_org: string;
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
  recent_complaints: {
    id: number;
    complaint_type: string;
    complaint_label: string;
    description: string;
    price_tagged: string | null;
    price_charged: string | null;
    status: string;
    created_at: string;
  }[];
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
  services: {
    id: number;
    name: string;
    service_type: string;
    service_label: string;
    duration_minutes: number;
    price: number | null;
  }[];
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

export type LabelValue = { value: string; label: string };
