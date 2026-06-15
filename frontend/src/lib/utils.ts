import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { ISSUE_STATUS_HINTS } from "@/lib/literaryCopy";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string) {
  return new Date(date).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Короткая дата для карточек объявлений */
export function formatShortDate(date: string) {
  return new Date(date).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
  });
}

export const STATUS_LABELS: Record<string, string> = {
  NEW: "Новое",
  UNDER_REVIEW: "На рассмотрении",
  ASSIGNED: "Назначено",
  IN_PROGRESS: "В работе",
  RESOLVED: "Решено",
  REJECTED: "Отклонено",
  ARCHIVED: "Архив",
};

export const ISSUE_ACTIVE_STATUSES = new Set([
  "NEW",
  "UNDER_REVIEW",
  "ASSIGNED",
  "IN_PROGRESS",
]);

export const ISSUE_DONE_STATUSES = new Set(["RESOLVED", "REJECTED", "ARCHIVED"]);

export function issueStatusHint(status: string): string {
  return ISSUE_STATUS_HINTS[status] || "";
}

export const STATUS_COLORS: Record<string, string> = {
  NEW: "bg-blue-100 text-blue-800",
  UNDER_REVIEW: "bg-yellow-100 text-yellow-800",
  ASSIGNED: "bg-purple-100 text-purple-800",
  IN_PROGRESS: "bg-orange-100 text-orange-800",
  RESOLVED: "bg-green-100 text-green-800",
  REJECTED: "bg-red-100 text-red-800",
  ARCHIVED: "bg-gray-100 text-gray-800",
};
