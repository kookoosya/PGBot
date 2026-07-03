/**
 * @vitest-environment jsdom
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EventsStatsRibbon } from "./EventsStatsRibbon";

vi.mock("@/lib/api/index", () => ({
  api: {
    getPublicEventsStats: vi.fn().mockResolvedValue({
      total_events: 12,
      by_region: { "Пушкинские Горы": 5, Псков: 7 },
      last_sync: "2026-07-03T08:00:00Z",
      event_sync_hours: 4,
      cinema_sync_hours: 8,
      full_sync_hours: 24,
    }),
  },
}));

describe("EventsStatsRibbon", () => {
  it("shows four-hour event sync interval", async () => {
    render(<EventsStatsRibbon />);
    expect(await screen.findByText(/авто каждые 4 ч/)).toBeTruthy();
    expect(screen.queryByText(/кино каждые/)).toBeNull();
  });
});
