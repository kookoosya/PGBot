import { describe, expect, it } from "vitest";
import { EVENT_REGION_FILTERS, parseRegionParam, regionFilterFromLabel } from "./eventRegionFilters";

describe("eventRegionFilters", () => {
  it("defaults to all regions", () => {
    expect(parseRegionParam(null)).toBe("all");
  });

  it("parses URL region param", () => {
    expect(parseRegionParam("pskov")).toBe("pskov");
    expect(parseRegionParam("all")).toBe("all");
  });

  it("lists three region filters", () => {
    expect(EVENT_REGION_FILTERS.map((f) => f.id)).toEqual(["all", "pushkin_gory", "pskov"]);
  });

  it("maps region labels back to filter ids", () => {
    expect(regionFilterFromLabel("Псков")).toBe("pskov");
    expect(regionFilterFromLabel("Пушкинские Горы")).toBe("pushkin_gory");
    expect(regionFilterFromLabel("Москва")).toBeNull();
  });
});
