import { describe, expect, it } from "vitest";

import type { PublicEvent } from "@/lib/api/types/events";

import { buildCategoryFilters } from "./utils";

function event(partial: Partial<PublicEvent> & Pick<PublicEvent, "id" | "title">): PublicEvent {
  return {
    id: partial.id,
    title: partial.title,
    description: partial.description ?? null,
    starts_at: partial.starts_at ?? "2026-07-01T18:00:00Z",
    ends_at: partial.ends_at ?? null,
    location: partial.location ?? null,
    region: partial.region ?? "pushkin_gory",
    region_label: partial.region_label ?? "Пушкинские Горы",
    category: partial.category ?? "culture",
    category_label: partial.category_label ?? "Культура",
    source: partial.source ?? "manual",
    source_url: partial.source_url ?? null,
    genre: partial.genre ?? null,
    poster_url: partial.poster_url ?? null,
    is_featured: partial.is_featured ?? false,
  };
}

describe("buildCategoryFilters", () => {
  it("lists Pushkin Hills categories first, then others alphabetically", () => {
    const filters = buildCategoryFilters([
      event({ id: 1, title: "A", region_label: "Псков", category_label: "Кино" }),
      event({ id: 2, title: "B", region_label: "Пушкинские Горы", category_label: "Ярмарка" }),
      event({ id: 3, title: "C", region_label: "Пушкинские Горы", category_label: "Концерт" }),
      event({ id: 4, title: "D", region_label: "Псков", category_label: "Спорт" }),
    ]);
    expect(filters).toEqual(["Концерт", "Ярмарка", "Кино", "Спорт"]);
  });

  it("returns empty list when no categories", () => {
    expect(buildCategoryFilters([])).toEqual([]);
  });
});
