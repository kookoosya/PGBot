import { describe, expect, it } from "vitest";
import {
  FESTIVAL_GARNECT,
  garnectEventsPath,
  isGarnectFestivalFilter,
  parseFestivalParam,
} from "./festivalFilters";

describe("festivalFilters", () => {
  it("parses garnect festival param", () => {
    expect(parseFestivalParam("garnect")).toBe(FESTIVAL_GARNECT);
    expect(parseFestivalParam(null)).toBeNull();
    expect(parseFestivalParam("other")).toBeNull();
  });

  it("detects garnect filter", () => {
    expect(isGarnectFestivalFilter(FESTIVAL_GARNECT)).toBe(true);
    expect(isGarnectFestivalFilter(null)).toBe(false);
  });

  it("builds events paths", () => {
    expect(garnectEventsPath()).toBe("/events?festival=garnect");
    expect(garnectEventsPath(true)).toBe("/vk/events?festival=garnect");
  });
});
