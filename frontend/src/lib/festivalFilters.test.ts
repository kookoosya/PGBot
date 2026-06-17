import { describe, expect, it } from "vitest";
import {
  absoluteGarnectEventsUrl,
  absoluteGarnectShareUrl,
  FESTIVAL_GARNECT,
  garnectEventsPath,
  garnectSharePath,
  GARNECT_FESTIVAL_TITLE,
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

  it("builds absolute garnect URL", () => {
    expect(absoluteGarnectEventsUrl("https://example.test")).toBe(
      "https://example.test/events?festival=garnect",
    );
    expect(absoluteGarnectShareUrl("https://example.test")).toBe(
      "https://example.test/share/festival/garnect",
    );
    expect(garnectSharePath()).toBe("/share/festival/garnect");
  });

  it("exports festival title", () => {
    expect(GARNECT_FESTIVAL_TITLE).toBe("Бугровский гарнец");
  });
});
