import { describe, expect, it } from "vitest";
import { buildEventsSourceHref, parseSourceParam } from "./eventSourceFilters";

describe("eventSourceFilters", () => {
  it("parses known source param", () => {
    expect(parseSourceParam("pushkinland")).toBe("pushkinland");
    expect(parseSourceParam("VK")).toBe("vk");
    expect(parseSourceParam(null)).toBeNull();
    expect(parseSourceParam("unknown_feed")).toBeNull();
  });

  it("builds events href", () => {
    expect(buildEventsSourceHref("pushkinland")).toBe("/events?source=pushkinland");
  });
});
