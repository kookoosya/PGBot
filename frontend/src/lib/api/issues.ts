/** Issues (complaints) API. */

import type { HttpClient } from "./client";
import type { Issue, IssueListResponse } from "./types";

export function createIssuesApi(client: HttpClient) {
  return {
    createIssue(data: {
      description: string;
      address?: string;
      category?: string;
      full_name?: string;
      phone?: string;
      website_url?: string;
    }) {
      return client.request<Issue>("/issues", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    getIssues(params?: Record<string, string>) {
      const query = params ? "?" + new URLSearchParams(params).toString() : "";
      return client.request<IssueListResponse>(`/issues${query}`);
    },

    getIssue(id: number) {
      return client.request<Issue>(`/issues/${id}`);
    },

    updateIssueStatus(id: number, status: string, resolution_text?: string) {
      return client.request<Issue>(`/issues/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status, resolution_text }),
      });
    },

    updateIssue(id: number, data: Partial<Issue>) {
      return client.request<Issue>(`/issues/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
  };
}

export type IssuesApi = ReturnType<typeof createIssuesApi>;
