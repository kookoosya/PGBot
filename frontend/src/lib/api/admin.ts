/** Admin panel API: users, stats, audit, departments. */

import type { HttpClient } from "./client";
import type { AuditLog, Department, FeedbackItem, Notification, Statistics, User, VisitStats } from "./types";

export function createAdminApi(client: HttpClient) {
  return {
    getUsers() {
      return client.request<User[]>("/users");
    },

    getDepartments() {
      return client.request<Department[]>("/departments");
    },

    createDepartment(data: Partial<Department>) {
      return client.request<Department>("/departments", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    getStatistics() {
      return client.request<Statistics>("/statistics");
    },

    getAdminFeedback() {
      return client.request<{ items: FeedbackItem[]; total: number }>("/feedback");
    },

    getVisitStats() {
      return client.request<VisitStats>("/visits/stats");
    },

    getAuditLogs() {
      return client.request<AuditLog[]>("/admin/audit-logs");
    },

    getNotifications() {
      return client.request<Notification[]>("/admin/notifications");
    },
  };
}

export type AdminApi = ReturnType<typeof createAdminApi>;
