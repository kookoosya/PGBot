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
