import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PublicInfo } from "@/lib/api/types";
import { PRIMARY_SITE_URL } from "@/lib/siteUrl";

let cachedInfo: PublicInfo | null = null;
let fetchPromise: Promise<PublicInfo> | null = null;

function loadPublicInfo(): Promise<PublicInfo> {
  if (cachedInfo) return Promise.resolve(cachedInfo);
  if (!fetchPromise) {
    fetchPromise = api
      .getPublicInfo()
      .then((info) => {
        cachedInfo = info;
        return info;
      })
      .catch(() => {
        fetchPromise = null;
        throw new Error("public info unavailable");
      });
  }
  return fetchPromise;
}

/** Публичные настройки портала (URL, VK и ссылки) */
export function useSiteInfo() {
  const [siteUrl, setSiteUrl] = useState(() =>
    typeof window !== "undefined" ? window.location.origin : PRIMARY_SITE_URL,
  );
  const [info, setInfo] = useState<PublicInfo | null>(cachedInfo);

  useEffect(() => {
    loadPublicInfo()
      .then((data) => {
        setInfo(data);
        if (data.site_url) setSiteUrl(data.site_url.replace(/\/$/, ""));
      })
      .catch(() => {});
  }, []);

  return { siteUrl, info };
}

export function resolveSiteUrl(fallback = PRIMARY_SITE_URL): string {
  if (typeof window !== "undefined") return window.location.origin;
  return cachedInfo?.site_url?.replace(/\/$/, "") ?? fallback;
}
