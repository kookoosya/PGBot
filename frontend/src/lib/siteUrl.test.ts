import { describe, expect, it } from "vitest";
import { CANONICAL_SITE_HOST, PRIMARY_SITE_URL, siteOrigin } from "./siteUrl";

describe("siteUrl", () => {
  it("uses sslip.io canonical host", () => {
    expect(CANONICAL_SITE_HOST).toContain("sslip.io");
    expect(PRIMARY_SITE_URL).toBe(`https://${CANONICAL_SITE_HOST}`);
  });

  it("siteOrigin falls back without window", () => {
    expect(siteOrigin()).toBe(PRIMARY_SITE_URL);
  });
});
