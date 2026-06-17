import { describe, expect, it } from "vitest";
import { formatSyncAge } from "./formatSyncAge";

describe("formatSyncAge", () => {
  it("returns placeholder when missing", () => {
    expect(formatSyncAge(null)).toBe("обновляется…");
  });

  it("formats recent sync", () => {
    const recent = new Date(Date.now() - 30 * 60 * 1000).toISOString();
    expect(formatSyncAge(recent)).toBe("только что");
  });

  it("formats hours ago", () => {
    const hoursAgo = new Date(Date.now() - 5 * 3_600_000).toISOString();
    expect(formatSyncAge(hoursAgo)).toBe("5 ч. назад");
  });
});
