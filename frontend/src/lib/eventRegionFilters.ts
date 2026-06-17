import type { EventRegion } from "@/lib/api";

export type RegionFilter = "all" | EventRegion;

export const EVENT_REGION_FILTERS: { id: RegionFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

export function parseRegionParam(value: string | null): RegionFilter {
  if (value === "pskov" || value === "pushkin_gory") return value;
  if (value === "all") return "all";
  return "all";
}

export function regionLabelFromFilterId(region: EventRegion): string {
  return region === "pskov" ? "Псков" : "Пушкинские Горы";
}
