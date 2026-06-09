/** Places, map and location-related API. */

import type { HttpClient } from "./client";
import type { ComplaintType, MapRoute, MapStats, PlaceDetail, PlaceListResponse, TaxiService } from "./types";

export function createPlacesApi(client: HttpClient) {
  return {
    getMapStats() {
      return client.request<MapStats>("/places/map/stats");
    },

    getPlaces(params?: Record<string, string>) {
      const query = params ? "?" + new URLSearchParams(params).toString() : "";
      return client.request<PlaceListResponse>(`/places${query}`);
    },

    getPlace(id: number) {
      return client.request<PlaceDetail>(`/places/${id}`);
    },

    getComplaintTypes() {
      return client.request<ComplaintType[]>("/places/complaint-types");
    },

    getMapReportTypes() {
      return client.request<ComplaintType[]>("/places/map-report-types");
    },

    getMapRoutes() {
      return client.request<MapRoute[]>("/places/routes");
    },

    getPlaceCategories() {
      return client.request<{ value: string; label: string }[]>("/places/categories");
    },

    getTaxiServices() {
      return client.request<TaxiService[]>("/places/taxi");
    },

    addReview(placeId: number, data: { rating: number; text?: string; author_name?: string }) {
      return client.request(`/places/${placeId}/reviews`, { method: "POST", body: JSON.stringify(data) });
    },

    addComplaint(placeId: number, data: Record<string, string | undefined>) {
      return client.request(`/places/${placeId}/complaints`, { method: "POST", body: JSON.stringify(data) });
    },
  };
}

export type PlacesApi = ReturnType<typeof createPlacesApi>;
