import { describe, expect, it } from "vitest";
import portalCopy from "../../../shared/portal_copy.json";
import {
  EMPTY_STATES,
  ISSUE_STATUS_EMOJI,
  ISSUE_STATUS_HINTS,
  LANDING_HERO_COPY,
  LANDING_SECTIONS_COPY,
  PAGE_SECTIONS_COPY,
  PORTAL_COPY_BRAND,
  PORTAL_COPY_LINKS,
  PORTAL_COPY_VK,
} from "./portalCopyShared";

describe("portalCopyShared ↔ shared/portal_copy.json", () => {
  it("syncs brand fields", () => {
    expect(PORTAL_COPY_BRAND.kicker).toBe(portalCopy.brand.kicker);
    expect(PORTAL_COPY_BRAND.tagline).toBe(portalCopy.brand.tagline);
  });

  it("syncs issue status hints", () => {
    expect(ISSUE_STATUS_HINTS).toEqual(portalCopy.issue_status_hints);
  });

  it("syncs issue status emoji", () => {
    expect(ISSUE_STATUS_EMOJI).toEqual(portalCopy.issue_status_emoji);
  });

  it("exposes portal links including map", () => {
    expect(PORTAL_COPY_LINKS.map).toBe(portalCopy.links.map);
    expect(PORTAL_COPY_LINKS.events).toBeTruthy();
  });

  it("exposes vk welcome body", () => {
    expect(PORTAL_COPY_VK.welcome_body).toBe(portalCopy.vk.welcome_body);
    expect(PORTAL_COPY_VK.welcome_body.length).toBeGreaterThan(20);
  });

  it("syncs empty states for key flows", () => {
    expect(EMPTY_STATES.events).toEqual(portalCopy.empty_states.events);
    expect(EMPTY_STATES.classifieds.title).toBeTruthy();
    expect(EMPTY_STATES.notFound.icon).toBe("🔍");
  });

  it("syncs landing hero copy", () => {
    expect(LANDING_HERO_COPY.lead).toBe(portalCopy.landing_hero.lead);
    expect(LANDING_HERO_COPY.cta_map).toBeTruthy();
  });

  it("syncs page sections for key flows", () => {
    expect(PAGE_SECTIONS_COPY.events).toEqual(portalCopy.page_sections.events);
    expect(PAGE_SECTIONS_COPY.signup.submitIdle).toBe(portalCopy.page_sections.signup.submitIdle);
    expect(PAGE_SECTIONS_COPY.cabinet.vkHint).toBeTruthy();
  });

  it("syncs landing sections with events pskov title", () => {
    expect(LANDING_SECTIONS_COPY.pskov.title).toBe(portalCopy.landing_sections.pskov.title);
    expect(LANDING_SECTIONS_COPY.pskov.title).toBe(PAGE_SECTIONS_COPY.events.pskov.title);
  });
});
