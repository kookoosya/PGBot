import { JOB_CATEGORY_IDS } from "@/lib/jobs";

/** Синхрон с backend SERVICE_CLASSIFIED_CATEGORIES */
export const SERVICE_CATEGORY_IDS = new Set([
  "garden",
  "firewood",
  "grass_mowing",
  "delivery",
  "handyman",
  "snow_removal",
  "construction",
  "construction_offer",
  "tutoring",
  "other",
]);

/** Синхрон с backend MARKET_CLASSIFIED_CATEGORIES */
export const MARKET_CATEGORY_IDS = new Set(["sale", "rent"]);

export type ClassifiedBoardId = "all" | "sale" | "services" | "help";

export interface ClassifiedBoard {
  id: ClassifiedBoardId;
  path: string;
  icon: string;
  title: string;
  lead: string;
  ribbonLabel: string;
}

export const CLASSIFIED_BOARDS: ClassifiedBoard[] = [
  {
    id: "all",
    path: "/classifieds",
    icon: "📋",
    title: "Вся доска",
    lead: "Все объявления посёлка, кроме вакансий.",
    ribbonLabel: "объявлений на доске",
  },
  {
    id: "sale",
    path: "/classifieds/sale",
    icon: "🏷️",
    title: "Продажа и аренда",
    lead: "Вещи, техника, жильё — купить или снять у соседей.",
    ribbonLabel: "объявлений о продаже и аренде",
  },
  {
    id: "services",
    path: "/classifieds/services",
    icon: "🛠",
    title: "Услуги",
    lead: "Покос, дрова, ремонт, доставка — работа руками соседей.",
    ribbonLabel: "объявлений об услугах",
  },
  {
    id: "help",
    path: "/classifieds/help",
    icon: "🤝",
    title: "Сосед помогает",
    lead: "Бесплатная взаимопомощь — без цены в объявлении.",
    ribbonLabel: "заявок о помощи",
  },
];

export function boardFromPath(pathname: string): ClassifiedBoardId {
  if (pathname.endsWith("/sale")) return "sale";
  if (pathname.endsWith("/services")) return "services";
  if (pathname.endsWith("/help")) return "help";
  return "all";
}

export function getBoard(id: ClassifiedBoardId): ClassifiedBoard {
  return CLASSIFIED_BOARDS.find((b) => b.id === id) ?? CLASSIFIED_BOARDS[0];
}

export function boardApiParams(board: ClassifiedBoardId): Record<string, string> {
  switch (board) {
    case "sale":
      return { market_only: "true" };
    case "services":
      return { services_only: "true" };
    case "help":
      return { neighbor_only: "true" };
    default:
      return { ads_only: "true" };
  }
}

export function categoriesForBoard(
  board: ClassifiedBoardId,
  all: { value: string; label: string }[],
): { value: string; label: string }[] {
  const nonJobs = all.filter((c) => !JOB_CATEGORY_IDS.has(c.value));
  switch (board) {
    case "sale":
      return nonJobs.filter((c) => MARKET_CATEGORY_IDS.has(c.value));
    case "services":
      return nonJobs.filter((c) => SERVICE_CATEGORY_IDS.has(c.value));
    case "help":
      return nonJobs.filter((c) => c.value === "neighbor_help");
    default:
      return nonJobs.filter((c) => c.value !== "neighbor_help");
  }
}

export function boardPathForCategory(category: string): string {
  if (category === "neighbor_help") return "/classifieds/help";
  if (MARKET_CATEGORY_IDS.has(category)) return "/classifieds/sale";
  if (SERVICE_CATEGORY_IDS.has(category)) return "/classifieds/services";
  return "/classifieds";
}

  { label: "Продажа и аренда", ids: MARKET_CATEGORY_IDS },
  { label: "Услуги", ids: SERVICE_CATEGORY_IDS },
  { label: "Взаимопомощь", ids: new Set(["neighbor_help"]) },
  { label: "Прочее", ids: new Set(["other"]) },
];
