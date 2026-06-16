/** Единственный рабочий прод-URL (до смены домена владельцем). */
export const CANONICAL_SITE_HOST = "192-210-213-135.sslip.io";
export const PRIMARY_SITE_URL = `https://${CANONICAL_SITE_HOST}`;

export function siteOrigin(): string {
  if (typeof window !== "undefined") return window.location.origin;
  return PRIMARY_SITE_URL;
}

export const SITE_URL = PRIMARY_SITE_URL;
