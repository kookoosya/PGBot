import type { MapFilterMode } from "@/lib/api/types/places";
export const MAP_CENTER: [number, number] = [57.0267, 28.91];

export const FALLBACK_MAP_MODES: MapFilterMode[] = [
  { id: "shops", label: "🛒 Магазины", category: null, shops_only: true, useful_only: false, show_taxi: false },
  { id: "pharmacy", label: "💊 Аптеки", category: "pharmacy", shops_only: false, useful_only: false, show_taxi: false },
  { id: "taxi", label: "🚕 Такси", category: null, shops_only: false, useful_only: false, show_taxi: true },
  { id: "useful", label: "🏦 Полезное", category: null, shops_only: false, useful_only: true, show_taxi: false },
  { id: "landmarks", label: "🏛 Достопримечательности", category: "culture", shops_only: false, useful_only: false, show_taxi: false },
];

export const CATEGORY_ICONS: Record<string, string> = {
  shop: "🛒", supermarket: "🏪", pharmacy: "💊", cafe: "☕",
  restaurant: "🍽", bank: "🏦", post: "📮", school: "🏫",
  hospital: "🏥", government: "🏛", transport: "🚌", culture: "🏛",
  hotel: "🏨", gas: "⛽", beauty: "💇", tyre: "🛞", auto: "🔧",
  taxi: "🚕", parking: "🅿️", other: "📍",
};

export const CATEGORY_COLORS: Record<string, string> = {
  shop: "#e67e22", supermarket: "#d35400", pharmacy: "#27ae60",
  cafe: "#8e44ad", restaurant: "#c0392b", bank: "#2980b9",
  post: "#1abc9c", school: "#3498db", hospital: "#e74c3c",
  government: "#2c3e50", transport: "#16a085", culture: "#9b59b6",
  tyre: "#34495e", auto: "#7f8c8d", gas: "#f39c12", hotel: "#16a085",
  beauty: "#e91e63", parking: "#95a5a6", taxi: "#f1c40f",
  other: "#1a5c3a",
};
