import { describe, expect, it } from "vitest";
import { absoluteEventShareUrl, eventSharePath } from "./eventShare";

describe("eventShare", () => {
  it("builds share paths", () => {
    expect(eventSharePath(42)).toBe("/share/events/42");
    expect(absoluteEventShareUrl("https://example.test", 42)).toBe(
      "https://example.test/share/events/42",
    );
  });
});
