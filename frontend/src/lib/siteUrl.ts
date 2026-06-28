/** Fallback до загрузки /public/info (см. hooks/useSiteInfo.ts). */
export const CANONICAL_SITE_HOST = "pushkinskie-gory.xyz";
export const RU_SITE_HOST = "pushkinskie-gory.ru";
export const PRIMARY_SITE_URL = `https://${CANONICAL_SITE_HOST}`;
export const RU_SITE_URL = `https://${RU_SITE_HOST}`;

export function siteOrigin(): string {
  if (typeof window !== "undefined") return window.location.origin;
  return PRIMARY_SITE_URL;
}
