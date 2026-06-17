export function formatPlaceNote(text: string | null | undefined): string | null {
  if (!text) return null;
  const cleaned = text
    .replace(/ · Данные из открытых источников — уточняйте перед визитом$/, "")
    .trim();
  return cleaned || null;
}
