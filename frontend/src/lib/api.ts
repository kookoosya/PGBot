const API_BASE = "/api/v1";

class ApiClient {
  private token: string | null = null;
  private userToken: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  setUserToken(token: string | null) {
    this.userToken = token;
  }

  private authHeader(): string | null {
    return this.token || this.userToken;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };
    const auth = this.authHeader();
    if (auth) {
      headers["Authorization"] = `Bearer ${auth}`;
    }

    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) return {} as T;
    return response.json();
  }

  login(username: string, password: string) {
    return this.request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  }

  getMe() {
    return this.request<User>("/auth/me");
  }

  ownerCheck() {
    return this.request<{ ok: boolean; username: string }>("/auth/owner-check");
  }

  changePassword(current_password: string, new_password: string) {
    return this.request<{ message: string }>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password }),
    });
  }

  createIssue(data: {
    description: string;
    address?: string;
    category?: string;
    full_name?: string;
    phone?: string;
    website_url?: string;
  }) {
    return this.request<Issue>("/issues", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  getIssues(params?: Record<string, string>) {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<IssueListResponse>(`/issues${query}`);
  }

  getIssue(id: number) {
    return this.request<Issue>(`/issues/${id}`);
  }

  updateIssueStatus(id: number, status: string, resolution_text?: string) {
    return this.request<Issue>(`/issues/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, resolution_text }),
    });
  }

  updateIssue(id: number, data: Partial<Issue>) {
    return this.request<Issue>(`/issues/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  getUsers() {
    return this.request<User[]>("/users");
  }

  getDepartments() {
    return this.request<Department[]>("/departments");
  }

  createDepartment(data: Partial<Department>) {
    return this.request<Department>("/departments", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  getStatistics() {
    return this.request<Statistics>("/statistics");
  }

  trackVisit(path: string) {
    return this.request<void>("/visits/track", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  }

  submitFeedback(data: { message: string; contact?: string; page?: string }) {
    return this.request<FeedbackItem>("/feedback", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  getAdminFeedback() {
    return this.request<{ items: FeedbackItem[]; total: number }>("/feedback");
  }

  getVisitStats() {
    return this.request<VisitStats>("/visits/stats");
  }

  getPublicInfo() {
    return this.request<PublicInfo>("/public/info");
  }

  getCategories() {
    return this.request<{ value: string; label: string }[]>("/categories");
  }

  getAuditLogs() {
    return this.request<AuditLog[]>("/admin/audit-logs");
  }

  getNotifications() {
    return this.request<Notification[]>("/admin/notifications");
  }

  // Public AI
  getAIUsage() {
    return this.request<UsageInfo>("/ai/usage");
  }

  getPaymentInfo() {
    return this.request<PaymentInfo>("/ai/payment-info");
  }

  getAIModels() {
    return this.request<AIModelsInfo>("/ai/models");
  }

  sendAIChat(message: string, history: { role: string; content: string }[], model?: string) {
    return this.request<ChatResponse>("/ai/chat", {
      method: "POST",
      body: JSON.stringify({ message, history, model }),
    });
  }

  generateAIImage(prompt: string, model: string) {
    return this.request<ImageGenResult>("/ai/generate-image", {
      method: "POST",
      body: JSON.stringify({ prompt, model }),
    });
  }

  registerResident(data: { username: string; email: string; password: string; full_name: string; phone?: string }) {
    return this.request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ ...data, role: "resident" }),
    });
  }

  registerOrganization(data: Record<string, string>) {
    return this.request<VerificationRequest>("/verification/register-organization", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Official registration
  registerOfficial(data: Record<string, string>) {
    return this.request<VerificationRequest>("/verification/register-official", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  getPendingVerifications() {
    return this.request<VerificationRequest[]>("/verification/pending");
  }

  approveVerification(id: number, note?: string) {
    return this.request(`/verification/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ note }),
    });
  }

  rejectVerification(id: number, note?: string) {
    return this.request(`/verification/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ note }),
    });
  }

  // Map / Places
  getMapStats() {
    return this.request<MapStats>("/places/map/stats");
  }

  getMapFilterModes() {
    return this.request<MapFilterMode[]>("/places/map/modes");
  }

  getWeather() {
    return this.request<WeatherResponse>("/weather");
  }

  getToday(region?: EventRegion) {
    const q = region ? `?region=${region}` : "";
    return this.request<TodayResponse>(`/public/today${q}`);
  }

  getPublicEvents(params?: {
    region?: EventRegion;
    category?: string;
    search?: string;
    limit?: string;
  }) {
    const query = params ? "?" + new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== "")) as Record<string, string>,
    ).toString() : "";
    return this.request<PublicEventListResponse>(`/public/events${query}`);
  }

  getPublicEvent(id: number) {
    return this.request<PublicEvent>(`/public/events/${id}`);
  }

  getAdminEvents(includeUnpublished = true) {
    const q = includeUnpublished ? "" : "?include_unpublished=false";
    return this.request<EventListResponse>(`/admin/events${q}`);
  }

  createEvent(data: EventCreate) {
    return this.request<EventItem>("/admin/events", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateEvent(id: number, data: Partial<EventCreate>) {
    return this.request<EventItem>(`/admin/events/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  syncVkEvents(region?: EventRegion) {
    const q = region ? `?region=${region}` : "";
    return this.request<EventSyncResult[]>(`/admin/events/sync-vk${q}`, {
      method: "POST",
    });
  }

  getVkModeration() {
    return this.request<VkModerationOverview>("/admin/vk-moderation");
  }

  unblockVkUser(vkUserId: number) {
    return this.request<{ ok: boolean; vk_user_id: number }>(`/admin/vk-moderation/${vkUserId}/unblock`, {
      method: "POST",
    });
  }

  syncKudagoEvents(region?: EventRegion) {
    const q = region ? `?region=${region}` : "";
    return this.request<EventSyncResult[]>(`/admin/events/sync-kudago${q}`, {
      method: "POST",
    });
  }

  syncTimepadEvents(region?: EventRegion) {
    const q = region ? `?region=${region}` : "";
    return this.request<EventSyncResult[]>(`/admin/events/sync-timepad${q}`, {
      method: "POST",
    });
  }

  syncAllEvents() {
    return this.request<EventSyncResult[]>(`/admin/events/sync-all`, {
      method: "POST",
    });
  }

  getMyIssues(params?: Record<string, string>) {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<IssueMyListResponse>(`/issues/my${query}`);
  }

  getPlaces(params?: Record<string, string>) {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<PlaceListResponse>(`/places${query}`);
  }

  getPlace(id: number) {
    return this.request<PlaceDetail>(`/places/${id}`);
  }

  getComplaintTypes() {
    return this.request<ComplaintType[]>("/places/complaint-types");
  }

  getMapReportTypes() {
    return this.request<ComplaintType[]>("/places/map-report-types");
  }

  getMapRoutes() {
    return this.request<MapRoute[]>("/places/routes");
  }

  getPlaceCategories() {
    return this.request<{ value: string; label: string }[]>("/places/categories");
  }

  getTaxiServices() {
    return this.request<TaxiService[]>("/places/taxi");
  }

  // Services
  getServiceTypes() {
    return this.request<{ value: string; label: string }[]>("/services/types");
  }

  getCatalogCategories() {
    return this.request<{ value: string; label: string }[]>("/catalog/categories");
  }

  getCatalogItems(params?: Record<string, string>) {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<CatalogItem[]>(`/catalog/items${q}`);
  }

  getAdminCatalogItems(internalOnly = false) {
    const q = internalOnly ? "?internal_only=true" : "";
    return this.request<CatalogItemAdmin[]>(`/catalog/admin/items${q}`);
  }

  createCatalogItem(data: CatalogItemCreate) {
    return this.request<CatalogItemAdmin>("/catalog/admin/items", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateCatalogItem(id: number, data: Partial<CatalogItemCreate> & { is_active?: boolean }) {
    return this.request<CatalogItemAdmin>(`/catalog/admin/items/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  deleteCatalogItem(id: number) {
    return this.request(`/catalog/admin/items/${id}`, { method: "DELETE" });
  }

  getServiceClassifieds(params?: Record<string, string>) {
    return this.getClassifieds({ ...params, services_only: "true", page_size: "50" });
  }

  getProviders(params?: Record<string, string>) {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<ServiceProvider[]>(`/services/providers${q}`);
  }

  getSlots(providerId: number, serviceId: number, date: string) {
    return this.request<SlotsResult>(`/services/providers/${providerId}/slots?service_id=${serviceId}&appointment_date=${date}`);
  }

  bookAppointment(providerId: number, data: Record<string, unknown>) {
    return this.request(`/services/providers/${providerId}/book`, { method: "POST", body: JSON.stringify(data) });
  }

  registerProvider(data: Record<string, unknown>) {
    return this.request("/services/register", { method: "POST", body: JSON.stringify(data) });
  }

  getPendingProviders() {
    return this.request<PendingProvider[]>("/services/providers/pending/list");
  }

  approveProvider(id: number) {
    return this.request(`/services/providers/${id}/approve`, { method: "POST" });
  }

  rejectProvider(id: number, reason?: string) {
    const q = reason ? `?reason=${encodeURIComponent(reason)}` : "";
    return this.request(`/services/providers/${id}/reject${q}`, { method: "POST" });
  }

  getMyProviderProfile() {
    return this.request<ProviderDetail>("/services/my/profile");
  }

  getMyAppointments() {
    return this.request<AppointmentItem[]>("/services/my/appointments");
  }

  getMyBusyBlocks() {
    return this.request<BusyBlock[]>("/services/my/busy");
  }

  addBusyBlock(data: { block_date: string; start_time: string; end_time: string; reason?: string }) {
    return this.request("/services/my/busy", { method: "POST", body: JSON.stringify(data) });
  }

  deleteBusyBlock(id: number) {
    return this.request(`/services/my/busy/${id}`, { method: "DELETE" });
  }

  updateMySchedule(schedule: { day_of_week: number; start_time: string; end_time: string; is_working: boolean }[]) {
    return this.request("/services/my/schedule", { method: "PATCH", body: JSON.stringify({ schedule }) });
  }

  getClassifiedCategories() {
    return this.request<{ value: string; label: string }[]>("/classifieds/categories");
  }

  getClassifiedPaymentInfo(phone?: string) {
    const q = phone ? `?phone=${encodeURIComponent(phone)}` : "";
    return this.request<ClassifiedPaymentInfo>(`/classifieds/payment-info${q}`);
  }

  getClassifiedMarketingStats() {
    return this.request<ClassifiedMarketingStats>("/classifieds/marketing-stats");
  }

  getClassifieds(params?: Record<string, string>) {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<{ items: ClassifiedAd[]; total: number; page?: number }>(`/classifieds${q}`);
  }

  getClassified(id: number) {
    return this.request<ClassifiedAd>(`/classifieds/${id}`);
  }

  getPendingClassifieds() {
    return this.request<ClassifiedPending[]>("/classifieds/pending");
  }

  createClassified(data: Record<string, unknown>) {
    return this.request<{ id: number; message: string }>("/classifieds", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  approveClassified(id: number) {
    return this.request(`/classifieds/${id}/approve`, { method: "POST" });
  }

  rejectClassified(id: number) {
    return this.request(`/classifieds/${id}/reject`, { method: "POST" });
  }

  addReview(placeId: number, data: { rating: number; text?: string; author_name?: string }) {
    return this.request(`/places/${placeId}/reviews`, { method: "POST", body: JSON.stringify(data) });
  }

  addComplaint(placeId: number, data: Record<string, string | undefined>) {
    return this.request(`/places/${placeId}/complaints`, { method: "POST", body: JSON.stringify(data) });
  }
}

export const api = new ApiClient();

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
  starts_at_label: string;
  ends_at_label?: string | null;
  location?: string | null;
  region: EventRegion;
  region_label: string;
  category: string;
  category_label: string;
  genre?: string | null;
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
  genre?: string | null;
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
  source?: string;
  region: string;
  fetched: number;
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
}
