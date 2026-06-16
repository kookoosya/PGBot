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

export interface PendingProvider {
  id: number;
  full_name: string;
  phone: string;
  address: string | null;
  services: string[];
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
