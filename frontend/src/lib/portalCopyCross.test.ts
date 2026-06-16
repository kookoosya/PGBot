import { describe, expect, it } from "vitest";
import portalCopy from "../../../shared/portal_copy.json";
import { ISSUE_STATUS_HINTS, PORTAL_COPY_BRAND } from "./portalCopyShared";

describe("portalCopyShared ↔ shared/portal_copy.json", () => {
  it("syncs brand fields", () => {
    expect(PORTAL_COPY_BRAND.kicker).toBe(portalCopy.brand.kicker);
    expect(PORTAL_COPY_BRAND.tagline).toBe(portalCopy.brand.tagline);
  });

  it("syncs issue status hints", () => {
    expect(ISSUE_STATUS_HINTS).toEqual(portalCopy.issue_status_hints);
  });
});
