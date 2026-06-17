export const FESTIVAL_GARNECT = "garnect" as const;

export type FestivalFilter = typeof FESTIVAL_GARNECT | null;

export const GARNECT_FESTIVAL_TITLE = "Бугровский гарнец";

export function parseFestivalParam(value: string | null): FestivalFilter {
  if (value === FESTIVAL_GARNECT) return FESTIVAL_GARNECT;
  return null;
}

export function garnectEventsPath(vk = false): string {
  return vk ? "/vk/events?festival=garnect" : "/events?festival=garnect";
}

export function garnectSharePath(): string {
  return "/share/festival/garnect";
}

export function absoluteGarnectEventsUrl(origin: string): string {
  return `${origin.replace(/\/$/, "")}${garnectEventsPath()}`;
}

export function absoluteGarnectShareUrl(origin: string): string {
  return `${origin.replace(/\/$/, "")}${garnectSharePath()}`;
}

export function isGarnectFestivalFilter(festival: FestivalFilter): festival is typeof FESTIVAL_GARNECT {
  return festival === FESTIVAL_GARNECT;
}
