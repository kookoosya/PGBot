/** Services, catalog and provider booking API. */

import type { HttpClient } from "./client";
import type {
  AppointmentItem,
  BusyBlock,
  CatalogItem,
  CatalogItemAdmin,
  CatalogItemCreate,
  PendingProvider,
  ProviderDetail,
  ServiceProvider,
  SlotsResult,
} from "./types";

export function createServicesApi(client: HttpClient) {
  return {
    getServiceTypes() {
      return client.request<{ value: string; label: string }[]>("/services/types");
    },

    getCatalogCategories() {
      return client.request<{ value: string; label: string }[]>("/catalog/categories");
    },

    getCatalogItems(params?: Record<string, string>) {
      const q = params ? "?" + new URLSearchParams(params).toString() : "";
      return client.request<CatalogItem[]>(`/catalog/items${q}`);
    },

    getAdminCatalogItems(internalOnly = false) {
      const q = internalOnly ? "?internal_only=true" : "";
      return client.request<CatalogItemAdmin[]>(`/catalog/admin/items${q}`);
    },

    createCatalogItem(data: CatalogItemCreate) {
      return client.request<CatalogItemAdmin>("/catalog/admin/items", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    updateCatalogItem(id: number, data: Partial<CatalogItemCreate> & { is_active?: boolean }) {
      return client.request<CatalogItemAdmin>(`/catalog/admin/items/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },

    deleteCatalogItem(id: number) {
      return client.request(`/catalog/admin/items/${id}`, { method: "DELETE" });
    },

    getProviders(params?: Record<string, string>) {
      const q = params ? "?" + new URLSearchParams(params).toString() : "";
      return client.request<ServiceProvider[]>(`/services/providers${q}`);
    },

    getSlots(providerId: number, serviceId: number, date: string) {
      return client.request<SlotsResult>(
        `/services/providers/${providerId}/slots?service_id=${serviceId}&appointment_date=${date}`,
      );
    },

    bookAppointment(providerId: number, data: Record<string, unknown>) {
      return client.request(`/services/providers/${providerId}/book`, { method: "POST", body: JSON.stringify(data) });
    },

    registerProvider(data: Record<string, unknown>) {
      return client.request("/services/register", { method: "POST", body: JSON.stringify(data) });
    },

    getPendingProviders() {
      return client.request<PendingProvider[]>("/services/providers/pending/list");
    },

    approveProvider(id: number) {
      return client.request(`/services/providers/${id}/approve`, { method: "POST" });
    },

    rejectProvider(id: number, reason?: string) {
      const q = reason ? `?reason=${encodeURIComponent(reason)}` : "";
      return client.request(`/services/providers/${id}/reject${q}`, { method: "POST" });
    },

    getMyProviderProfile() {
      return client.request<ProviderDetail>("/services/my/profile");
    },

    getMyAppointments() {
      return client.request<AppointmentItem[]>("/services/my/appointments");
    },

    getMyBusyBlocks() {
      return client.request<BusyBlock[]>("/services/my/busy");
    },

    addBusyBlock(data: { block_date: string; start_time: string; end_time: string; reason?: string }) {
      return client.request("/services/my/busy", { method: "POST", body: JSON.stringify(data) });
    },

    deleteBusyBlock(id: number) {
      return client.request(`/services/my/busy/${id}`, { method: "DELETE" });
    },

    updateMySchedule(schedule: { day_of_week: number; start_time: string; end_time: string; is_working: boolean }[]) {
      return client.request("/services/my/schedule", { method: "PATCH", body: JSON.stringify({ schedule }) });
    },
  };
}

export type ServicesApi = ReturnType<typeof createServicesApi>;
