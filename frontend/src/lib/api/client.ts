/** HTTP-клиент: fetch и Bearer-токены (admin / resident). */

export const API_BASE = "/api/v1";

export function formatApiErrorDetail(detail: unknown, status: number): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : ""))
      .filter(Boolean);
    if (messages.length > 0) return messages.join("; ");
  }
  return `HTTP ${status}`;
}

export class HttpClient {
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

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
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
      throw new Error(formatApiErrorDetail(error.detail, response.status));
    }

    if (response.status === 204) return {} as T;
    return response.json();
  }
}
