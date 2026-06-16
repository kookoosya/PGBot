import type { EventRegion, PublicEvent, TodayEventSnippet } from "@/lib/api";

export type ShowGroupable = {
  id: number;
  title: string;
  starts_at?: string;
  starts_at_label: string;
  ends_at_label?: string | null;
  location?: string | null;
  region?: EventRegion;
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

/** Merge API lists without duplicate ids (first occurrence wins). */
export function mergePublicEvents(...lists: PublicEvent[][]): PublicEvent[] {
  const seen = new Set<number>();
  const merged: PublicEvent[] = [];
  for (const list of lists) {
    for (const event of list) {
      if (seen.has(event.id)) continue;
      seen.add(event.id);
      merged.push(event);
    }
  }
  return merged;
}

export const EVENT_SOURCE_LABELS: Record<string, string> = {
  vk: "ВКонтакте",
  kudago: "KudaGo",
  timepad: "TimePad",
  orbilet: "Orbilet",
  kinopskov: "Kinopskov60",
  mirage: "Мираж Синема",
  silver: "Silver Cinema",
  proculture: "PRO.Культура",
  kdc: "КДЦ Пушкиногорье",
  pushkinland: "Пушкинский заповедник",
  informpskov: "ИнформПсков",
  pln: "ПЛН Псков",
  drampush: "Театр драмы",
  manual: "Организатор",
};

const CINEMA_AFISHA_SOURCES = new Set([
  "orbilet",
  "kinopskov",
  "mirage",
  "silver",
  "kudago",
  "timepad",
]);

const CULTURE_LIKE_TITLE =
  /культурно-просветительн|мероприяти[ея]|петрушкин|спектакл|концерт|выставк|праздник|фестиваль|экскурс|лекци|ярмарк|театр|музе[йя]|мастер[- ]класс|постановк|игра\s*«/i;

const GENERIC_CINEMA_TITLE =
  /^(кино|киноафиша|афиша|сеанс|сеансы|кинотеатр|кинопоказ|премьера недели|новинки кино|в прокате)$/i;

export function eventSourceLabel(source: string | null | undefined): string {
  if (!source) return "Организатор";
  return EVENT_SOURCE_LABELS[source] || source;
}

export function regionChipClass(regionLabel: string): string {
  if (regionLabel === "Псков") return "events-region-chip events-region-chip--pskov";
  return "events-region-chip events-region-chip--pushkin";
}

export function isCinemaEvent(event: { category?: string }): boolean {
  return event.category === "cinema";
}

/** Only real film sessions — not miscategorized culture events. */
export function isRealCinemaEvent(event: EventCardEvent): boolean {
  if (!isCinemaEvent(event)) return false;

  const title = event.title.trim();
  if (CULTURE_LIKE_TITLE.test(title)) return false;
  if (GENERIC_CINEMA_TITLE.test(title)) return false;

  const source = "source" in event ? event.source : null;
  if (source && CINEMA_AFISHA_SOURCES.has(source)) return true;

  if (event.genre) return true;
  if (/[«»"]/.test(title)) return true;

  return false;
}

export function regionLabelFromFilter(region: EventRegion): string {
  return region === "pskov" ? "Псков" : "Пушкинские Горы";
}

function collapseRepeatedPhrases(text: string): string {
  const parts = text
    .split(/(?<=[.!?…])\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
  if (parts.length <= 1) return text.trim();

  const seen = new Set<string>();
  const unique: string[] = [];
  for (const part of parts) {
    const key = part.toLowerCase().replace(/\s+/g, " ");
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(part);
  }
  return unique.join(" ").trim();
}

export function eventTeaser(event: EventCardEvent, maxLen = 120): string {
  if (!event.description) return "";

  let text = event.description
    .replace(/^Жанр:\s*[^.]+\.\s*/i, "")
    .replace(/\s*Билеты на orbilet\.ru\.?\s*/gi, "")
    .replace(/\s*Билеты на mirage\.ru\.?\s*/gi, "")
    .replace(/\s*Билеты на silvercinema\.ru\.?\s*/gi, "")
    .trim();

  const title = event.title.replace(/"/g, "").trim();
  const quotedTitle = `"${title}"`;
  for (const prefix of [quotedTitle, title, `«${title}»`]) {
    while (text.startsWith(prefix)) {
      text = text.slice(prefix.length).replace(/^[.\s"«»]+/, "").trim();
    }
  }

  text = text
    .replace(/^Место:\s*[^.]+\.\s*/gi, "")
    .replace(/^Сеанс:\s*[^.]+\.\s*/gi, "")
    .replace(/^Зал №\d+\.\s*/gi, "")
    .trim();

  if (event.location) {
    const location = event.location.trim();
    const escaped = location.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    text = text.replace(new RegExp(`^${escaped}[.\\s]+`, "i"), "").trim();
  }

  text = collapseRepeatedPhrases(text);

  if (!text || text === event.location) return "";
  if (text.length <= maxLen) return text;
  return `${text.slice(0, maxLen - 1).trim()}…`;
}

const STOCK_GALLERY_PREFIX = "/images/gallery/";

const GARNEC_PROGRAM_RE = /бугровский\s+гарнец|«бугровский\s+гарнец»/i;

export function isDisplayablePoster(
  posterUrl: string | null | undefined,
  category?: string,
): boolean {
  if (!posterUrl?.trim()) return false;
  const lower = posterUrl.toLowerCase();
  if (posterUrl.startsWith(STOCK_GALLERY_PREFIX)) return false;
  if (lower.includes("no-poster") || lower.includes("no_poster")) return false;
  if (category === "cinema" && posterUrl.startsWith("/images/")) return false;
  return true;
}

/** Performance from a multi-show festival program (e.g. Бугровский гарнец on pushkinland). */
export function isGarnectProgramEvent(event: Pick<ShowGroupable, "title" | "source" | "source_url">): boolean {
  if (event.source !== "pushkinland") return false;
  const title = event.title.toLowerCase();
  const url = (event.source_url || "").toLowerCase();
  return GARNEC_PROGRAM_RE.test(title) || (title.includes("гарнец") && url.includes("/news/"));
}

export function partitionGarnectProgram<T extends ShowGroupable & { id: number }>(
  events: T[],
): { program: T[]; rest: T[] } {
  const program = events.filter(isGarnectProgramEvent).sort((a, b) =>
    (a.starts_at || a.starts_at_label).localeCompare(b.starts_at || b.starts_at_label),
  );
  if (program.length < 2) {
    return { program: [], rest: events };
  }
  const programIds = new Set(program.map((event) => event.id));
  return {
    program,
    rest: events.filter((event) => !programIds.has(event.id)),
  };
}

function formatFestivalDay(isoDate: string): string {
  const [year, month, day] = isoDate.split("-");
  if (!year || !month || !day) return isoDate;
  return `${day}.${month}`;
}

export function formatFestivalDateRange(events: Pick<ShowGroupable, "starts_at" | "starts_at_label">[]): string {
  const days = [...new Set(events.map((event) => event.starts_at?.slice(0, 10)).filter(Boolean) as string[])].sort();
  if (!days.length) {
    return events[0]?.starts_at_label?.split("·")[0]?.trim() || "";
  }
  if (days.length === 1) return formatFestivalDay(days[0]);
  return `${formatFestivalDay(days[0])} – ${formatFestivalDay(days[days.length - 1])}`;
}

export function pluralPerformances(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return "спектакль";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return "спектакля";
  return "спектаклей";
}

/** True when the festival starts within ``withinDays`` (incl. today and in-progress). */
export function isFestivalImminent(
  events: Pick<ShowGroupable, "starts_at" | "starts_at_label">[],
  withinDays = 3,
): boolean {
  if (!events.length) return false;
  const now = Date.now();
  const graceMs = 24 * 60 * 60 * 1000;
  const horizon = now + withinDays * 24 * 60 * 60 * 1000;

  for (const event of events) {
    if (!event.starts_at) continue;
    const start = Date.parse(event.starts_at);
    if (Number.isNaN(start)) continue;
    if (start >= now - graceMs && start <= horizon) {
      return true;
    }
  }
  return false;
}

export function extractEventTimeLabel(event: Pick<ShowGroupable, "starts_at" | "starts_at_label">): string {
  if (event.starts_at_label.includes("·")) {
    return event.starts_at_label.split("·").pop()?.trim() || event.starts_at_label;
  }
  if (event.starts_at) {
    const date = new Date(event.starts_at);
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
    }
  }
  return event.starts_at_label;
}

export function shortenFestivalPerformanceTitle(title: string): string {
  return title.replace(/\s*—\s*Бугровский гарнец\s*$/i, "").trim();
}

export type FestivalDayGroup<T extends ShowGroupable & { id: number }> = {
  dayKey: string;
  dayLabel: string;
  items: T[];
};

export function groupFestivalPerformancesByDay<T extends ShowGroupable & { id: number }>(
  events: T[],
): FestivalDayGroup<T>[] {
  const buckets = new Map<string, T[]>();

  for (const event of events) {
    const dayKey = event.starts_at?.slice(0, 10) || event.starts_at_label.split("·")[0]?.trim() || "unknown";
    const list = buckets.get(dayKey) ?? [];
    list.push(event);
    buckets.set(dayKey, list);
  }

  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([dayKey, items]) => {
      items.sort((a, b) => (a.starts_at || a.starts_at_label).localeCompare(b.starts_at || b.starts_at_label));
      const sample = items[0]?.starts_at;
      const dayLabel = sample
        ? new Date(sample).toLocaleDateString("ru-RU", { weekday: "short", day: "numeric", month: "long" })
        : dayKey;
      return { dayKey, dayLabel, items };
    });
}

export const FESTIVAL_COMPACT_LIST_THRESHOLD = 5;

export function groupEventsByShow<T extends ShowGroupable>(events: T[]): (T & { extraSessions?: T[] })[] {
  const buckets = new Map<string, T[]>();
  for (const event of events) {
    const key = `${event.title}|${event.location || ""}|${event.region || event.region_label || ""}`;
    const list = buckets.get(key) ?? [];
    list.push(event);
    buckets.set(key, list);
  }

  const grouped: (T & { extraSessions?: T[] })[] = [];
  for (const list of buckets.values()) {
    list.sort((a, b) => (a.starts_at || a.starts_at_label).localeCompare(b.starts_at || b.starts_at_label));
    const [first, ...rest] = list;
    grouped.push(rest.length ? { ...first, extraSessions: rest } : first);
  }
  return grouped.sort((a, b) =>
    (a.starts_at || a.starts_at_label).localeCompare(b.starts_at || b.starts_at_label),
  );
}

export function formatExtraSessions(sessions: Pick<ShowGroupable, "starts_at_label">[]): string {
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
