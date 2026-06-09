/** Public endpoints: site info, feedback, visit tracking. */

import type { HttpClient } from "./client";
import type { FeedbackItem, PublicInfo } from "./types";

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
  };
}

export type PublicApi = ReturnType<typeof createPublicApi>;
