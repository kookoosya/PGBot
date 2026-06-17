import { describe, expect, it } from "vitest";
import { canSyncEventSource } from "./AdminEventSourcesPanel";

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

describe("canSyncEventSource", () => {
  const base = {
    id: "timepad",
    label: "TimePad",
    published_count: 0,
    token_hint: null,
    last_synced_at: null,
  };

  it("blocks sync when token is missing", () => {
    expect(canSyncEventSource({ ...base, health: "needs_token" })).toBe(false);
  });

  it("allows sync for ready and group_token_only", () => {
    expect(canSyncEventSource({ ...base, health: "ready" })).toBe(true);
    expect(canSyncEventSource({ ...base, health: "group_token_only" })).toBe(true);
  });
});
