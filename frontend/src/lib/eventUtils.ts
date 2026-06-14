import type { EventRegion, PublicEvent, TodayEventSnippet } from "@/lib/api";

export type EventCardEvent = PublicEvent | TodayEventSnippet;

export const EVENT_SOURCE_LABELS: Record<string, string> = {
  vk: "ВКонтакте",
  kudago: "KudaGo",
  timepad: "TimePad",
  manual: "Организатор",
};

export const CATEGORY_ICONS: Record<string, string> = {
  cinema: "🎬",
  culture: "🎭",
  holiday: "🎉",
  sport: "⚽",
  education: "📚",
  tourism: "🧭",
  community: "👥",
  other: "📅",
};

export function eventSourceLabel(source: string | null | undefined): string {
  if (!source) return "Организатор";
  return EVENT_SOURCE_LABELS[source] || source;
}

export function categoryIcon(category: string): string {
  return CATEGORY_ICONS[category] || CATEGORY_ICONS.other;
}

export function regionChipClass(regionLabel: string): string {
  if (regionLabel === "Псков") return "events-region-chip events-region-chip--pskov";
  return "events-region-chip events-region-chip--pushkin";
}

export function regionLabelFromFilter(region: EventRegion): string {
  return region === "pskov" ? "Псков" : "Пушкинские Горы";
}

export function eventTeaser(event: EventCardEvent, maxLen = 140): string {
  if (event.description) {
    const text = event.description.replace(/^Жанр:\s*[^.]+\.\s*/i, "").trim();
    if (text.length <= maxLen) return text;
    return `${text.slice(0, maxLen - 1).trim()}…`;
  }
  return "";
}

export function isCinemaEvent(event: EventCardEvent): boolean {
  return event.category === "cinema";
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
