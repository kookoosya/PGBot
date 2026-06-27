import { describe, expect, it } from "vitest";
import { PRIMARY_SITE_URL } from "@/lib/siteUrl";
import { resolveSiteUrl } from "@/hooks/useSiteInfo";

describe("useSiteInfo", () => {
  it("resolveSiteUrl falls back when cache empty", () => {
    expect(resolveSiteUrl("https://example.test")).toBe("https://example.test");
  });

  it("PRIMARY_SITE_URL is canonical", () => {
    expect(PRIMARY_SITE_URL).toContain("pushkinskie-gory.xyz");
  });
});
