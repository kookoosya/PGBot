/** Auth, registration and verification API. */

import type { AuthScope, HttpClient } from "./client";
import type { User, VerificationRequest } from "./types";

export function createAuthApi(client: HttpClient) {
  return {
    login(username: string, password: string, scope: AuthScope = "user") {
      return client.request<{ access_token: string }>(`/auth/login?client=${scope}`, {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
    },

    getMe() {
      return client.request<User>("/auth/me");
    },

    ownerCheck() {
      return client.request<{ ok: boolean; username: string }>("/auth/owner-check");
    },

    changePassword(current_password: string, new_password: string) {
      return client.request<{ message: string }>("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password, new_password }),
      });
    },

    registerResident(data: { username: string; email: string; password: string; full_name: string; phone?: string }) {
      return client.request<User>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ ...data, role: "resident" }),
      });
    },

    registerOrganization(data: Record<string, string>) {
      return client.request<VerificationRequest>("/verification/register-organization", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    registerOfficial(data: Record<string, string>) {
      return client.request<VerificationRequest>("/verification/register-official", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    getPendingVerifications() {
      return client.request<VerificationRequest[]>("/verification/pending");
    },

    approveVerification(id: number, note?: string) {
      return client.request(`/verification/${id}/approve`, {
        method: "POST",
        body: JSON.stringify({ note }),
      });
    },

    rejectVerification(id: number, note?: string) {
      return client.request(`/verification/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({ note }),
      });
    },
  };
}

export type AuthApi = ReturnType<typeof createAuthApi>;
