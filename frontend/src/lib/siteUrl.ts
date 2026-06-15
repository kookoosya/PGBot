/** Канонический URL портала (прод на sslip.io; .ru отложен) */
export const PRIMARY_SITE_URL = "https://192-210-213-135.sslip.io";

export function siteOrigin(): string {
  if (typeof window !== "undefined") return window.location.origin;
  return PRIMARY_SITE_URL;
}

export const SITE_URL = PRIMARY_SITE_URL;
