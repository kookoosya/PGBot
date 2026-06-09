/** Classified ads API. */

import type { HttpClient } from "./client";
import type { ClassifiedAd, ClassifiedMarketingStats, ClassifiedPaymentInfo, ClassifiedPending } from "./types";

export function createClassifiedsApi(client: HttpClient) {
  return {
    getClassifiedCategories() {
      return client.request<{ value: string; label: string }[]>("/classifieds/categories");
    },

    getClassifiedPaymentInfo(phone?: string) {
      const q = phone ? `?phone=${encodeURIComponent(phone)}` : "";
      return client.request<ClassifiedPaymentInfo>(`/classifieds/payment-info${q}`);
    },

    getClassifiedMarketingStats() {
      return client.request<ClassifiedMarketingStats>("/classifieds/marketing-stats");
    },

    getClassifieds(params?: Record<string, string>) {
      const q = params ? "?" + new URLSearchParams(params).toString() : "";
      return client.request<{ items: ClassifiedAd[]; total: number; page?: number }>(`/classifieds${q}`);
    },

    getClassified(id: number) {
      return client.request<ClassifiedAd>(`/classifieds/${id}`);
    },

    getPendingClassifieds() {
      return client.request<ClassifiedPending[]>("/classifieds/pending");
    },

    createClassified(data: Record<string, unknown>) {
      return client.request<{ id: number; message: string }>("/classifieds", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    approveClassified(id: number) {
      return client.request(`/classifieds/${id}/approve`, { method: "POST" });
    },

    rejectClassified(id: number) {
      return client.request(`/classifieds/${id}/reject`, { method: "POST" });
    },
  };
}

export type ClassifiedsApi = ReturnType<typeof createClassifiedsApi>;
