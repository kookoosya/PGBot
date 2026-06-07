const API_BASE = "/api/v1";

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
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

  getCategories() {
    return this.request<{ value: string; label: string }[]>("/categories");
  }

  getAuditLogs() {
    return this.request<AuditLog[]>("/admin/audit-logs");
  }

  getNotifications() {
    return this.request<Notification[]>("/admin/notifications");
  }
}

export const api = new ApiClient();

export interface User {
  id: number;
  username: string;
  email: string | null;
  full_name: string | null;
  role: string;
  department_id: number | null;
  is_active: boolean;
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
