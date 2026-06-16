/** VK Mini App API. */

import type { HttpClient } from "./client";

export function createVkApi(client: HttpClient) {
  return {
    vkMiniAppAuth(launchParams: string) {
      return client.request<{ access_token: string; token_type: string; user: Record<string, unknown> }>(
        "/vk/auth",
        {
          method: "POST",
          body: JSON.stringify({ launch_params: launchParams }),
        },
      );
    },
  };
}

export type VkApi = ReturnType<typeof createVkApi>;
