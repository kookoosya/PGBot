export interface CategoryVisual {
  icon: string;
  gradient: string;
}

export const CLASSIFIED_CATEGORY_VISUALS: Record<string, CategoryVisual> = {
  garden: { icon: "🌱", gradient: "linear-gradient(135deg, #365314 0%, #65a30d 100%)" },
  firewood: { icon: "🪵", gradient: "linear-gradient(135deg, #5c3d2e 0%, #8b5a3c 100%)" },
  grass_mowing: { icon: "🌿", gradient: "linear-gradient(135deg, #2d5a27 0%, #4a8f3f 100%)" },
  delivery: { icon: "🚚", gradient: "linear-gradient(135deg, #1e4d6b 0%, #3a7ca5 100%)" },
  handyman: { icon: "🔧", gradient: "linear-gradient(135deg, #4a4a4a 0%, #6b6b6b 100%)" },
  snow_removal: { icon: "❄️", gradient: "linear-gradient(135deg, #4a6fa5 0%, #8bb8e8 100%)" },
  construction: { icon: "🏗", gradient: "linear-gradient(135deg, #8b6914 0%, #c9a227 100%)" },
  construction_vacancy: { icon: "👷", gradient: "linear-gradient(135deg, #b45309 0%, #f59e0b 100%)" },
  construction_offer: { icon: "🔨", gradient: "linear-gradient(135deg, #7c2d12 0%, #c2410c 100%)" },
  tutoring: { icon: "📚", gradient: "linear-gradient(135deg, #312e81 0%, #6366f1 100%)" },
  rent: { icon: "🏠", gradient: "linear-gradient(135deg, #14532d 0%, #22c55e 100%)" },
  sale: { icon: "📦", gradient: "linear-gradient(135deg, #713f12 0%, #d97706 100%)" },
  job: { icon: "💼", gradient: "linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%)" },
  job_tourism: { icon: "🏨", gradient: "linear-gradient(135deg, #0f766e 0%, #14b8a6 100%)" },
  job_trade: { icon: "🛒", gradient: "linear-gradient(135deg, #b45309 0%, #fbbf24 100%)" },
  job_agriculture: { icon: "🌾", gradient: "linear-gradient(135deg, #365314 0%, #84cc16 100%)" },
  job_seasonal: { icon: "☀️", gradient: "linear-gradient(135deg, #c2410c 0%, #fb923c 100%)" },
  job_driver: { icon: "🚗", gradient: "linear-gradient(135deg, #1e3a8a 0%, #60a5fa 100%)" },
  job_jkh: { icon: "🔧", gradient: "linear-gradient(135deg, #374151 0%, #9ca3af 100%)" },
  job_culture: { icon: "🏛", gradient: "linear-gradient(135deg, #581c87 0%, #a855f7 100%)" },
  job_social: { icon: "🏥", gradient: "linear-gradient(135deg, #be123c 0%, #fb7185 100%)" },
  job_education: { icon: "🏫", gradient: "linear-gradient(135deg, #1d4ed8 0%, #93c5fd 100%)" },
  other: { icon: "📋", gradient: "linear-gradient(135deg, #3f3f46 0%, #71717a 100%)" },
};

export function getCategoryVisual(category: string): CategoryVisual {
  return CLASSIFIED_CATEGORY_VISUALS[category] ?? CLASSIFIED_CATEGORY_VISUALS.other;
}
