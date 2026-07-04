import { describe, expect, it } from "vitest";
import { formatApiErrorDetail } from "./client";

describe("formatApiErrorDetail", () => {
  it("returns string detail as-is", () => {
    expect(formatApiErrorDetail("Укажите имя и телефон", 400)).toBe("Укажите имя и телефон");
  });

  it("formats FastAPI validation array", () => {
    expect(
      formatApiErrorDetail(
        [{ type: "string_too_short", loc: ["body", "description"], msg: "String should have at least 5 characters" }],
        422,
      ),
    ).toBe("String should have at least 5 characters");
  });

  it("falls back to HTTP status", () => {
    expect(formatApiErrorDetail(undefined, 500)).toBe("HTTP 500");
  });
});
