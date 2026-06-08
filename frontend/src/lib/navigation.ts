import { User } from "./api";
import { isOfficialUser } from "./userAuth";

/** Куда вести пользователя после входа или по клику на имя в шапке */
export function getUserHomePath(user: User | null | undefined): string {
  if (!user) return "/cabinet/login";
  if (isOfficialUser(user)) return "/official";
  if (user.role === "service_provider") return "/services/cabinet";
  return "/cabinet";
}

export function getUserHomeLabel(user: User | null | undefined): string {
  if (!user) return "Вход";
  if (isOfficialUser(user)) return "Портал служб";
  if (user.role === "service_provider") return "Кабинет мастера";
  return "Личный кабинет";
}

export type NavSection = {
  to: string;
  label: string;
  icon: string;
  end?: boolean;
};

/** Основные разделы портала — единый список для табов и подвала */
export const MAIN_SECTIONS: NavSection[] = [
  { to: "/", label: "Главная", icon: "🏠", end: true },
  { to: "/map", label: "Карта", icon: "🗺" },
  { to: "/classifieds", label: "Объявления", icon: "📋" },
  { to: "/jobs", label: "Работа", icon: "💼" },
  { to: "/services", label: "Услуги", icon: "🛠" },
  { to: "/complaints", label: "Жалобы", icon: "⚠️" },
  { to: "/wishes", label: "Пожелания", icon: "💡" },
  { to: "/ai", label: "ИИ", icon: "🤖" },
];

export type QuickNavItem = NavSection & {
  desc: string;
  color: string;
};

/** Быстрые карточки на главной — расширение MAIN_SECTIONS без дублирования путей */
const QUICK_NAV_META: Record<string, { desc: string; color: string; icon?: string }> = {
  "/map": { desc: "Магазины и службы", color: "quick-nav-map" },
  "/classifieds": { desc: "От жителей", color: "quick-nav-ads" },
  "/services": { desc: "Мастера", color: "quick-nav-svc", icon: "💇" },
  "/ai": { desc: "Помощник", color: "quick-nav-ai" },
};

export const QUICK_NAV_SECTIONS: QuickNavItem[] = MAIN_SECTIONS.filter(
  (section) => section.to in QUICK_NAV_META,
).map((section) => {
  const meta = QUICK_NAV_META[section.to];
  return {
    ...section,
    icon: meta.icon ?? section.icon,
    desc: meta.desc,
    color: meta.color,
  };
});

/** Дополнительные карточки мастера (не входят в MAIN_SECTIONS) */
export const QUICK_NAV_EXTRA: QuickNavItem[] = [
  { to: "/services/cabinet", label: "Мастер", icon: "📅", desc: "Кабинет", color: "quick-nav-cab" },
  { to: "/services/register", label: "Стать мастером", icon: "✨", desc: "Регистрация", color: "quick-nav-reg" },
];
