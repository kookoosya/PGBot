import { describe, expect, it } from "vitest";
import { formatTodayUpdatedAt } from "@/hooks/useToday";

describe("useToday helpers", () => {
  it("formatTodayUpdatedAt returns empty for invalid date", () => {
    expect(formatTodayUpdatedAt("not-a-date")).toBe("");
  });

  it("formatTodayUpdatedAt formats ISO timestamps", () => {
    const formatted = formatTodayUpdatedAt("2026-06-16T10:30:00Z");
    expect(formatted).toMatch(/\d{2}\.\d{2}/);
    expect(formatted).toMatch(/\d{2}:\d{2}/);
  });
});
