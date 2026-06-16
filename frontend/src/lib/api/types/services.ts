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
