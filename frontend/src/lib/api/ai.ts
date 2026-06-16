/** Public AI chat API. */

import type { HttpClient } from "./client";
import type { AIModelsInfo, ChatResponse, ImageGenResult, PaymentInfo, UsageInfo } from "./types";

export function createAiApi(client: HttpClient) {
  return {
    getAIUsage() {
      return client.request<UsageInfo>("/ai/usage");
    },

    getPaymentInfo() {
      return client.request<PaymentInfo>("/ai/payment-info");
    },

    getAIModels() {
      return client.request<AIModelsInfo>("/ai/models");
    },

    sendAIChat(message: string, history: { role: string; content: string }[], model?: string) {
      return client.request<ChatResponse>("/ai/chat", {
        method: "POST",
        body: JSON.stringify({ message, history, model }),
      });
    },

    generateAIImage(prompt: string, model: string) {
      return client.request<ImageGenResult>("/ai/generate-image", {
        method: "POST",
        body: JSON.stringify({ prompt, model }),
      });
    },
  };
}

export type AiApi = ReturnType<typeof createAiApi>;
