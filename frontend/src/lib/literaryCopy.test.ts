import { describe, expect, it } from "vitest";
import { EMPTY_STATES, LANDING_SECTIONS, PAGE_SECTIONS } from "./literaryCopy";
import { PORTAL_COPY_BRAND } from "./portalCopyShared";

describe("literaryCopy", () => {
  it("exposes page sections with non-empty titles", () => {
    expect(PAGE_SECTIONS.events.title.length).toBeGreaterThan(3);
    expect(PAGE_SECTIONS.classifieds.title.length).toBeGreaterThan(3);
    expect(PAGE_SECTIONS.services.title.length).toBeGreaterThan(3);
  });

  it("keeps landing and events pskov copy aligned", () => {
    expect(LANDING_SECTIONS.pskov.title).toBe(PAGE_SECTIONS.events.pskov.title);
  });

  it("provides empty states for key flows", () => {
    expect(EMPTY_STATES.events.title).toBeTruthy();
    expect(EMPTY_STATES.classifieds.title).toBeTruthy();
    expect(EMPTY_STATES.cinema.title).toBeTruthy();
  });

  it("syncs brand kicker with shared portal copy", () => {
    expect(PORTAL_COPY_BRAND.kicker).toMatch(/Пушкин/i);
  });
});
