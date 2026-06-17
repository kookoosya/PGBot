export const FESTIVAL_GARNECT = "garnect" as const;

export type FestivalFilter = typeof FESTIVAL_GARNECT | null;

export function parseFestivalParam(value: string | null): FestivalFilter {
  if (value === FESTIVAL_GARNECT) return FESTIVAL_GARNECT;
  return null;
}

export function garnectEventsPath(vk = false): string {
  return vk ? "/vk/events?festival=garnect" : "/events?festival=garnect";
}

export function isGarnectFestivalFilter(festival: FestivalFilter): festival is typeof FESTIVAL_GARNECT {
  return festival === FESTIVAL_GARNECT;
}
