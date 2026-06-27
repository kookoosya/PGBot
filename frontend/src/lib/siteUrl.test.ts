import { describe, expect, it } from "vitest";
import { CANONICAL_SITE_HOST, PRIMARY_SITE_URL, siteOrigin } from "./siteUrl";

describe("siteUrl", () => {
  it("uses canonical production host", () => {
    expect(CANONICAL_SITE_HOST).toBe("pushkinskie-gory.xyz");
    expect(PRIMARY_SITE_URL).toBe(`https://${CANONICAL_SITE_HOST}`);
  });

  it("siteOrigin falls back without window", () => {
    expect(siteOrigin()).toBe(PRIMARY_SITE_URL);
  });
});
