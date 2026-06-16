/** Events API: public listings and admin sync. */

import type { HttpClient } from "./client";
import type {
  EventCreate,
  EventItem,
  EventListResponse,
  EventRegion,
  EventSyncResult,
  PublicEvent,
  PublicEventListResponse,
} from "./types";

export function createEventsApi(client: HttpClient) {
  return {
    getPublicEvents(params?: { region?: EventRegion; search?: string; limit?: string }) {
      const query = params
        ? "?" +
          new URLSearchParams(
            Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== "")) as Record<
              string,
              string
            >,
          ).toString()
        : "";
      return client.request<PublicEventListResponse>(`/public/events${query}`);
    },

    getPublicEvent(id: number) {
      return client.request<PublicEvent>(`/public/events/${id}`);
    },

    getAdminEvents(includeUnpublished = true) {
      const q = includeUnpublished ? "" : "?include_unpublished=false";
      return client.request<EventListResponse>(`/admin/events${q}`);
    },

    createEvent(data: EventCreate) {
      return client.request<EventItem>("/admin/events", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    updateEvent(id: number, data: Partial<EventCreate>) {
      return client.request<EventItem>(`/admin/events/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },

    syncVkEvents(region?: EventRegion) {
      const q = region ? `?region=${region}` : "";
      return client.request<EventSyncResult[]>(`/admin/events/sync-vk${q}`, {
        method: "POST",
      });
    },

    syncKudagoEvents(region?: EventRegion) {
      const q = region ? `?region=${region}` : "";
      return client.request<EventSyncResult[]>(`/admin/events/sync-kudago${q}`, {
        method: "POST",
      });
    },
  };
}

export type EventsApi = ReturnType<typeof createEventsApi>;
