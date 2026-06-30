import { describe, expect, it } from "vitest";
import { showsAds, showsCatalog, showsProviders } from "./servicesBoard";

describe("servicesBoard", () => {
  it("shows all sections on all tab", () => {
    expect(showsCatalog("all")).toBe(true);
    expect(showsAds("all")).toBe(true);
    expect(showsProviders("all")).toBe(true);
  });

  it("isolates sections on specific tabs", () => {
    expect(showsCatalog("catalog")).toBe(true);
    expect(showsAds("catalog")).toBe(false);
    expect(showsProviders("providers")).toBe(true);
    expect(showsCatalog("providers")).toBe(false);
  });
});
