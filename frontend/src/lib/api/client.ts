/** HTTP-клиент: fetch, auth tokens, refresh on 401. */

export const API_BASE = "/api/v1";

export type AuthScope = "admin" | "user";

type AuthState = { token: string; scope: AuthScope } | null;

export class HttpClient {
  private token: string | null = null;
  private userToken: string | null = null;
  private refreshPromises: Partial<Record<AuthScope, Promise<boolean>>> = {};

  setToken(token: string | null) {
    this.token = token;
  }

  setUserToken(token: string | null) {
    this.userToken = token;
  }

  private authState(): AuthState {
    if (this.token) return { token: this.token, scope: "admin" };
    if (this.userToken) return { token: this.userToken, scope: "user" };
    return null;
  }

  private applyAccessToken(scope: AuthScope, accessToken: string) {
    if (scope === "admin") {
      this.token = accessToken;
    } else {
      this.userToken = accessToken;
    }
  }

  private clearScope(scope: AuthScope) {
    if (scope === "admin") {
      this.token = null;
    } else {
      this.userToken = null;
    }
  }

  private defaultHeaders(extra?: Record<string, string>): Record<string, string> {
    return {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
      ...(extra ?? {}),
    };
  }

  private isAuthPath(path: string): boolean {
    return path.startsWith("/auth/login") || path.startsWith("/auth/refresh") || path.startsWith("/auth/logout");
  }

  async refreshAccessToken(scope: AuthScope): Promise<boolean> {
    const pending = this.refreshPromises[scope];
    if (pending) return pending;

    const promise = (async () => {
      try {
        const response = await fetch(`${API_BASE}/auth/refresh?client=${scope}`, {
          method: "POST",
          credentials: "include",
          headers: this.defaultHeaders(),
        });
        if (!response.ok) {
          this.clearScope(scope);
          return false;
        }
        const data = (await response.json()) as { access_token: string };
        this.applyAccessToken(scope, data.access_token);
        return true;
      } catch {
        this.clearScope(scope);
        return false;
      }
    })();

    this.refreshPromises[scope] = promise;
    try {
      return await promise;
    } finally {
      delete this.refreshPromises[scope];
    }
  }

  async logoutAuth(scope: AuthScope): Promise<void> {
    try {
      await fetch(`${API_BASE}/auth/logout?client=${scope}`, {
        method: "POST",
        credentials: "include",
        headers: this.defaultHeaders(),
      });
    } finally {
      this.clearScope(scope);
    }
  }

  async request<T>(path: string, options: RequestInit = {}, retried = false): Promise<T> {
    const headers = this.defaultHeaders(options.headers as Record<string, string> | undefined);
    const auth = this.authState();
    if (auth) {
      headers["Authorization"] = `Bearer ${auth.token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      credentials: "include",
    });

    if (response.status === 401 && !retried && auth && !this.isAuthPath(path)) {
      const refreshed = await this.refreshAccessToken(auth.scope);
      if (refreshed) {
        return this.request<T>(path, options, true);
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) return {} as T;
    return response.json();
  }
}
