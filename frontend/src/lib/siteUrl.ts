/** Основной домен портала (купленный .ru) */
export const PRIMARY_SITE_URL = "https://pushkinskie-gory.ru";

export function siteOrigin(): string {
  if (typeof window !== "undefined") return window.location.origin;
  return PRIMARY_SITE_URL;
}

export const SITE_URL = PRIMARY_SITE_URL;
