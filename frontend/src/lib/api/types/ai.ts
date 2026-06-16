export interface PaymentInfo {
  card_number: string;
  card_holder?: string;
  bank_name?: string;
  amount_suggested: number;
  message: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatResponse {
  reply: string;
  remaining: number;
  daily_limit: number;
  limit_reached: boolean;
  model?: string;
}

export interface AIModelOption {
  id: string;
  label: string;
  provider: string;
  desc?: string;
  fast?: boolean;
  smart?: boolean;
}

export interface AIStatus {
  ready: boolean;
  chat_provider: string;
  image_provider: string;
  pollinations_configured: boolean;
  openrouter_configured?: boolean;
  gemini_configured: boolean;
  providers?: string[];
  message: string;
  limits?: {
    site_daily: number;
    site_note: string;
    providers_note: string;
  };
}

export interface AIModelsInfo {
  chat_models: AIModelOption[];
  image_models: AIModelOption[];
  capabilities: string[];
  status?: AIStatus;
}

export interface ImageGenResult {
  url: string | null;
  model: string;
  prompt: string;
  provider?: string;
  error?: string;
}

export interface UsageInfo {
  used: number;
  remaining: number;
  daily_limit: number;
  payment_info?: PaymentInfo;
}
