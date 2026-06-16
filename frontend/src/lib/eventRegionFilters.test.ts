import { describe, expect, it } from "vitest";
import { EVENT_REGION_FILTERS, parseRegionParam } from "./eventRegionFilters";

describe("eventRegionFilters", () => {
  it("defaults to pushkin_gory", () => {
    expect(parseRegionParam(null)).toBe("pushkin_gory");
  });

  it("parses URL region param", () => {
    expect(parseRegionParam("pskov")).toBe("pskov");
    expect(parseRegionParam("all")).toBe("all");
  });

  it("lists three region filters", () => {
    expect(EVENT_REGION_FILTERS.map((f) => f.id)).toEqual(["all", "pushkin_gory", "pskov"]);
  });
});
