/** gmxreply.com заблокирован в РФ (семейство GMX) — основной адрес без VPN */
export const PRIMARY_SITE_URL = "https://192-210-213-135.sslip.io";
export const FALLBACK_HTTP_URL = "http://192.210.213.135:8088";
export const LEGACY_BLOCKED_URL = "https://pushkiny.gmxreply.com";

export function siteOrigin(): string {
  if (typeof window !== "undefined") return window.location.origin;
  return PRIMARY_SITE_URL;
}

export const SITE_URL = PRIMARY_SITE_URL;
