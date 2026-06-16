import { describe, expect, it } from "vitest";
import {
  eventSourceLabel,
  eventTeaser,
  formatExtraSessions,
  groupEventsByShow,
  isDisplayablePoster,
  isRealCinemaEvent,
  regionChipClass,
  regionLabelFromFilter,
} from "./eventUtils";

const cinemaOrbilet = {
  id: 1,
  title: "«Мандалорец и Грогу»",
  category: "cinema",
  source: "orbilet",
  starts_at_label: "16 июн, 19:00",
  description: "«Мандалорец и Грогу». Билеты на orbilet.ru.",
};

const cultureMiscategorized = {
  id: 2,
  title: "Концерт у НКЦ",
  category: "cinema",
  starts_at_label: "17 июн, 18:00",
};

describe("isRealCinemaEvent", () => {
  it("accepts orbilet sessions with quoted titles", () => {
    expect(isRealCinemaEvent(cinemaOrbilet)).toBe(true);
  });

  it("rejects culture events miscategorized as cinema", () => {
    expect(isRealCinemaEvent(cultureMiscategorized)).toBe(false);
  });
});

describe("groupEventsByShow", () => {
  it("merges duplicate showtimes into extraSessions", () => {
    const grouped = groupEventsByShow([
      { id: 1, title: "Фильм", location: "Мираж", starts_at_label: "16 июн, 19:00" },
      { id: 2, title: "Фильм", location: "Мираж", starts_at_label: "16 июн, 21:30" },
    ]);
    expect(grouped).toHaveLength(1);
    expect(grouped[0].extraSessions).toHaveLength(1);
  });
});

describe("eventTeaser", () => {
  it("strips ticket boilerplate and title prefix", () => {
    const text = eventTeaser(cinemaOrbilet, 200);
    expect(text).not.toContain("orbilet.ru");
    expect(text).not.toMatch(/^«Мандалорец/);
  });
});

describe("formatExtraSessions", () => {
  it("lists up to three extra session labels", () => {
    const text = formatExtraSessions([
      { starts_at_label: "19:00" },
      { starts_at_label: "21:30" },
      { starts_at_label: "23:00" },
      { starts_at_label: "01:00" },
    ]);
    expect(text).toContain("19:00");
    expect(text).toContain("ещё 1");
  });
});

describe("eventSourceLabel", () => {
  it("maps known sources and falls back for unknown", () => {
    expect(eventSourceLabel("vk")).toBe("ВКонтакте");
    expect(eventSourceLabel("custom_feed")).toBe("custom_feed");
    expect(eventSourceLabel(null)).toBe("Организатор");
  });
});

describe("region helpers", () => {
  it("returns chip class by region label", () => {
    expect(regionChipClass("Псков")).toContain("pskov");
    expect(regionChipClass("Пушкинские Горы")).toContain("pushkin");
  });

  it("maps filter id to label", () => {
    expect(regionLabelFromFilter("pskov")).toBe("Псков");
    expect(regionLabelFromFilter("pushkin_gory")).toBe("Пушкинские Горы");
  });
});

describe("isDisplayablePoster", () => {
  it("rejects stock gallery placeholders for cinema", () => {
    expect(isDisplayablePoster("/images/gallery/cinema.jpg", "cinema")).toBe(false);
    expect(isDisplayablePoster("https://cdn.example.com/poster.jpg", "cinema")).toBe(true);
  });
});
