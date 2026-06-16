/** Public endpoints: site info, weather, today, feedback, visit tracking. */

import type { HttpClient } from "./client";
import type { EventRegion, FeedbackItem, PublicInfo, TodayResponse, WeatherResponse } from "./types";

export function createPublicApi(client: HttpClient) {
  return {
    getPublicInfo() {
      return client.request<PublicInfo>("/public/info");
    },

    getCategories() {
      return client.request<{ value: string; label: string }[]>("/categories");
    },

    trackVisit(path: string) {
      return client.request<void>("/visits/track", {
        method: "POST",
        body: JSON.stringify({ path }),
      });
    },

    submitFeedback(data: { message: string; contact?: string; page?: string }) {
      return client.request<FeedbackItem>("/feedback", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    getWeather() {
      return client.request<WeatherResponse>("/weather");
    },

    getToday(region?: EventRegion) {
      const q = region ? `?region=${region}` : "";
      return client.request<TodayResponse>(`/public/today${q}`);
    },
  };
}

export type PublicApi = ReturnType<typeof createPublicApi>;
