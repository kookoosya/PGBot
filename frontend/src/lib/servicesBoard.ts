export type ServiceTabId = "all" | "catalog" | "ads" | "providers";

export interface ServiceTab {
  id: ServiceTabId;
  icon: string;
  title: string;
}

export const SERVICE_TABS: ServiceTab[] = [
  { id: "all", icon: "🪶", title: "Всё" },
  { id: "catalog", icon: "📍", title: "Справочник" },
  { id: "ads", icon: "🤝", title: "От соседей" },
  { id: "providers", icon: "💇", title: "Запись" },
];

export function showsCatalog(tab: ServiceTabId): boolean {
  return tab === "all" || tab === "catalog";
}

export function showsAds(tab: ServiceTabId): boolean {
  return tab === "all" || tab === "ads";
}

export function showsProviders(tab: ServiceTabId): boolean {
  return tab === "all" || tab === "providers";
}
