import type { EventRegion, PublicEvent, TodayEventSnippet } from "@/lib/api";

export type ShowGroupable = {
  id: number;
  title: string;
  starts_at: string;
  starts_at_label: string;
  ends_at_label?: string | null;
  location?: string | null;
  region: EventRegion;
  category?: string;
  category_label?: string;
  genre?: string | null;
  poster_url?: string | null;
  description?: string | null;
  region_label?: string;
  source?: string | null;
  source_url?: string | null;
};

export type GroupedPublicEvent = ShowGroupable & {
  extraSessions?: ShowGroupable[];
};

export type EventCardEvent = PublicEvent | TodayEventSnippet | GroupedPublicEvent;

export const EVENT_SOURCE_LABELS: Record<string, string> = {
  vk: "ВКонтакте",
  kudago: "KudaGo",
  timepad: "TimePad",
  orbilet: "Orbilet",
  proculture: "PRO.Культура",
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

export function isCinemaEvent(event: { category?: string }): boolean {
  return event.category === "cinema";
}

const STOCK_GALLERY_PREFIX = "/images/gallery/";

/** Real poster URL — not a site gallery placeholder wrongly used for cinema. */
export function isDisplayablePoster(
  posterUrl: string | null | undefined,
  category?: string,
): boolean {
  if (!posterUrl?.trim()) return false;
  if (posterUrl.startsWith(STOCK_GALLERY_PREFIX)) return false;
  if (category === "cinema" && posterUrl.startsWith("/images/")) return false;
  return true;
}

/** One card per title+venue; extra showtimes attached to the nearest session. */
export function groupEventsByShow<T extends ShowGroupable>(events: T[]): (T & { extraSessions?: T[] })[] {
  const buckets = new Map<string, T[]>();
  for (const event of events) {
    const key = `${event.title}|${event.location || ""}|${event.region}`;
    const list = buckets.get(key) ?? [];
    list.push(event);
    buckets.set(key, list);
  }

  const grouped: (T & { extraSessions?: T[] })[] = [];
  for (const list of buckets.values()) {
    list.sort((a, b) => a.starts_at.localeCompare(b.starts_at));
    const [first, ...rest] = list;
    grouped.push(rest.length ? { ...first, extraSessions: rest } : first);
  }
  return grouped.sort((a, b) => a.starts_at.localeCompare(b.starts_at));
}

export function formatExtraSessions(sessions: Pick<PublicEvent, "starts_at_label">[]): string {
  if (!sessions.length) return "";
  const labels = sessions.slice(0, 3).map((s) => s.starts_at_label);
  const tail = sessions.length > 3 ? ` и ещё ${sessions.length - 3}` : "";
  return `Ещё сеансы: ${labels.join(", ")}${tail}`;
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
