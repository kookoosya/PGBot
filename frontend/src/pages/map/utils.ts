export function formatPlaceNote(text: string | null | undefined): string | null {
  if (!text) return null;
  const cleaned = text
    .replace(/ · Данные из открытых источников — уточняйте перед визитом$/, "")
    .trim();
  return cleaned || null;
}

export function formatSyncAge(iso: string | null): string {
  if (!iso) return "обновляется…";
  const diff = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diff / 3_600_000);
  if (hours < 1) return "только что";
  if (hours < 24) return `${hours} ч. назад`;
  return `${Math.floor(hours / 24)} дн. назад`;
}
