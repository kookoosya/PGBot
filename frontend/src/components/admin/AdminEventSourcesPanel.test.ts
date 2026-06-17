import { describe, expect, it } from "vitest";

function healthLabel(health: "ready" | "group_token_only" | "needs_token"): string {
  if (health === "ready") return "Готов";
  if (health === "group_token_only") return "Только своя группа";
  return "Нужен токен";
}

describe("admin event source labels", () => {
  it("maps health statuses", () => {
    expect(healthLabel("ready")).toBe("Готов");
    expect(healthLabel("group_token_only")).toBe("Только своя группа");
    expect(healthLabel("needs_token")).toBe("Нужен токен");
  });
});
