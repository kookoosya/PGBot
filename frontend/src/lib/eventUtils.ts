import type { EventRegion } from "@/lib/api";

export const EVENT_SOURCE_LABELS: Record<string, string> = {
  vk: "ВКонтакте",
  kudago: "KudaGo",
  manual: "Организатор",
};

export function eventSourceLabel(source: string | null | undefined): string {
  if (!source) return "Организатор";
  return EVENT_SOURCE_LABELS[source] || source;
}

export function regionChipClass(regionLabel: string): string {
  if (regionLabel === "Псков") return "events-region-chip events-region-chip--pskov";
  return "events-region-chip events-region-chip--pushkin";
}

export function regionLabelFromFilter(region: EventRegion): string {
  return region === "pskov" ? "Псков" : "Пушкинские Горы";
}

export async function shareEventUrl(title: string): Promise<string | null> {
  const url = window.location.href;
  try {
    if (navigator.share) {
      await navigator.share({ title: `${title} — Пушкинские Горы`, url });
      return null;
    }
    await navigator.clipboard.writeText(url);
    return "Ссылка скопирована";
  } catch {
    return "Не удалось поделиться";
  }
}
