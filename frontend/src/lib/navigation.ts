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
