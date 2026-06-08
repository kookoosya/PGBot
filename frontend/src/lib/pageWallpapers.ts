import { VILLAGE_PHOTOS } from "@/lib/pushkin";

export type PageWallpaper = {
  webp: string;
  url: string;
  label: string;
};

const photos = VILLAGE_PHOTOS;

/** Обои для каждого раздела портала */
export const PAGE_WALLPAPERS: Record<string, PageWallpaper> = {
  "/": { ...photos[0], label: "Михайловское" },
  "/map": { ...photos[2], label: "Посёлок" },
  "/classifieds": { ...photos[3], label: "Памятник" },
  "/services": { ...photos[4], label: "Тригорское" },
  "/complaints": { ...photos[1], label: "Лавра" },
  "/wishes": { ...photos[5], label: "Петровское" },
  "/ai": { ...photos[0], label: "Михайловское" },
  "/register": { ...photos[4], label: "Тригорское" },
  "/cabinet/login": { ...photos[2], label: "Посёлок" },
  "/cabinet": { ...photos[3], label: "Памятник" },
  "/official": { ...photos[1], label: "Лавра" },
};

export function wallpaperForPath(pathname: string): PageWallpaper {
  const base = pathname.split("?")[0];
  if (PAGE_WALLPAPERS[base]) return PAGE_WALLPAPERS[base];
  if (base.startsWith("/map")) return PAGE_WALLPAPERS["/map"];
  if (base.startsWith("/classifieds")) return PAGE_WALLPAPERS["/classifieds"];
  if (base.startsWith("/services")) return PAGE_WALLPAPERS["/services"];
  if (base.startsWith("/complaints")) return PAGE_WALLPAPERS["/complaints"];
  if (base.startsWith("/wishes")) return PAGE_WALLPAPERS["/wishes"];
  if (base.startsWith("/ai")) return PAGE_WALLPAPERS["/ai"];
  if (base.startsWith("/register") || base.startsWith("/signup")) return PAGE_WALLPAPERS["/register"];
  return PAGE_WALLPAPERS["/"];
}
