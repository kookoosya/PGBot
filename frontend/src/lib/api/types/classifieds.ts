import type { PaymentInfo } from "./ai";

export interface ClassifiedMarketingStats {
  total_ads: number;
  total_views: number;
  avg_views_per_ad: number;
  monthly_reach_estimate: number;
  placement_fee: number;
  period_days: number;
  category_stats: { category: string; label: string; ads: number; views: number }[];
  roi_examples: {
    service: string;
    ad_cost: number;
    clients: number;
    avg_check: number;
    income: number;
    roi_percent: number;
  }[];
  weekly_views: { day: string; views: number }[];
}

export interface ClassifiedPaymentInfo {
  card_number: string;
  amount: number;
  period_days: number;
  message: string;
  free_limit: number;
  free_used: number;
  free_remaining: number;
  requires_payment: boolean;
}

export interface ClassifiedAd {
  id: number;
  category: string;
  category_label: string;
  title: string;
  description: string;
  price: number | null;
  price_unit: string | null;
  phone: string;
  author_name: string;
  address: string | null;
  created_at: string;
}

export interface ClassifiedMineAd extends ClassifiedAd {
  payment_status: string;
  is_active: boolean;
}

export interface ClassifiedPending extends ClassifiedAd {
  payment_status: string;
  payment_reference: string | null;
  placement_fee: number;
  contact_vk?: string | null;
}

export type { PaymentInfo };
