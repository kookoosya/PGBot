export interface CategoryVisual {
  icon: string;
  image: string;
  gradient: string;
}

export const CLASSIFIED_CATEGORY_VISUALS: Record<string, CategoryVisual> = {
  firewood: {
    icon: "🪵",
    image: "https://images.unsplash.com/photo-1513836279014-a89f7a76bd86?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #5c3d2e 0%, #8b5a3c 100%)",
  },
  grass_mowing: {
    icon: "🌿",
    image: "https://images.unsplash.com/photo-1558904541-efa843a96f01?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #2d5a27 0%, #4a8f3f 100%)",
  },
  delivery: {
    icon: "🚚",
    image: "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #1e4d6b 0%, #3a7ca5 100%)",
  },
  handyman: {
    icon: "🔧",
    image: "https://images.unsplash.com/photo-1504147799335-fc865a5bec2f?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #4a4a4a 0%, #6b6b6b 100%)",
  },
  snow_removal: {
    icon: "❄️",
    image: "https://images.unsplash.com/photo-1491003603938-6f8926a82aa4?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #4a6fa5 0%, #8bb8e8 100%)",
  },
  construction: {
    icon: "🏗",
    image: "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #8b6914 0%, #c9a227 100%)",
  },
  construction_vacancy: {
    icon: "👷",
    image: "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #b45309 0%, #f59e0b 100%)",
  },
  construction_offer: {
    icon: "🔨",
    image: "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #7c2d12 0%, #c2410c 100%)",
  },
  tutoring: {
    icon: "📚",
    image: "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #312e81 0%, #6366f1 100%)",
  },
  rent: {
    icon: "🏠",
    image: "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #14532d 0%, #22c55e 100%)",
  },
  sale: {
    icon: "📦",
    image: "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #713f12 0%, #d97706 100%)",
  },
  job: {
    icon: "💼",
    image: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%)",
  },
  other: {
    icon: "📋",
    image: "https://images.unsplash.com/photo-1457369804613-52cbabdbefbc?w=400&h=280&fit=crop",
    gradient: "linear-gradient(135deg, #3f3f46 0%, #71717a 100%)",
  },
};

export function getCategoryVisual(category: string): CategoryVisual {
  return CLASSIFIED_CATEGORY_VISUALS[category] ?? CLASSIFIED_CATEGORY_VISUALS.other;
}
