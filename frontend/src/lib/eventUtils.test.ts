import { describe, expect, it } from "vitest";
import {
  eventSourceLabel,
  eventTeaser,
  extractEventTimeLabel,
  formatExtraSessions,
  formatFestivalDateRange,
  groupEventsByShow,
  groupFestivalPerformancesByDay,
  isDisplayablePoster,
  isRealCinemaEvent,
  isFestivalImminent,
  partitionGarnectProgram,
  pluralPerformances,
  regionChipClass,
  regionLabelFromFilter,
  shortenFestivalPerformanceTitle,
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

describe("partitionGarnectProgram", () => {
  const garnectA = {
    id: 1,
    title: "«Рассказы Девицы К. И. Т. » — Бугровский гарнец",
    source: "pushkinland",
    source_url: "https://pushkinland.ru/2018/news/news26/news57.php",
    starts_at: "2026-06-19T10:15:00+03:00",
    starts_at_label: "19.06.2026 · 10:15",
  };
  const garnectB = {
    id: 2,
    title: "«Пиратские анекдоты» — Бугровский гарнец",
    source: "pushkinland",
    source_url: "https://pushkinland.ru/2018/news/news26/news57.php",
    starts_at: "2026-06-20T10:15:00+03:00",
    starts_at_label: "20.06.2026 · 10:15",
  };
  const other = {
    id: 3,
    title: "День языков народов России",
    source: "pushkinland",
    starts_at: "2026-06-18T12:00:00+03:00",
    starts_at_label: "18.06.2026 · 12:00",
  };

  it("groups garnet performances and leaves other pushkin events separate", () => {
    const { program, rest } = partitionGarnectProgram([other, garnectB, garnectA]);
    expect(program).toHaveLength(2);
    expect(rest).toHaveLength(1);
    expect(rest[0].id).toBe(3);
  });

  it("returns all events in rest when only one garnet performance", () => {
    const { program, rest } = partitionGarnectProgram([garnectA, other]);
    expect(program).toHaveLength(0);
    expect(rest).toHaveLength(2);
  });
});

describe("formatFestivalDateRange", () => {
  it("formats multi-day range", () => {
    const text = formatFestivalDateRange([
      { starts_at: "2026-06-19T10:00:00+03:00", starts_at_label: "19.06.2026 · 10:00" },
      { starts_at: "2026-06-20T11:00:00+03:00", starts_at_label: "20.06.2026 · 11:00" },
    ]);
    expect(text).toBe("19.06 – 20.06");
  });
});

describe("pluralPerformances", () => {
  it("uses russian plural forms", () => {
    expect(pluralPerformances(1)).toBe("спектакль");
    expect(pluralPerformances(3)).toBe("спектакля");
    expect(pluralPerformances(14)).toBe("спектаклей");
  });
});

describe("isFestivalImminent", () => {
  it("returns true when a performance starts within 3 days", () => {
    const soon = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString();
    expect(isFestivalImminent([{ starts_at: soon, starts_at_label: "скоро" }])).toBe(true);
  });

  it("returns false for distant festival", () => {
    const later = new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString();
    expect(isFestivalImminent([{ starts_at: later, starts_at_label: "позже" }])).toBe(false);
  });
});

describe("groupFestivalPerformancesByDay", () => {
  it("groups performances by calendar day and sorts by time", () => {
    const groups = groupFestivalPerformancesByDay([
      {
        id: 2,
        title: "Вечерний",
        starts_at: "2026-06-20T18:00:00+03:00",
        starts_at_label: "20.06.2026 · 18:00",
      },
      {
        id: 1,
        title: "Утренний",
        starts_at: "2026-06-19T10:15:00+03:00",
        starts_at_label: "19.06.2026 · 10:15",
      },
    ]);
    expect(groups).toHaveLength(2);
    expect(groups[0].items[0].id).toBe(1);
    expect(groups[1].items[0].id).toBe(2);
  });
});

describe("festival schedule helpers", () => {
  it("extracts time from starts_at_label", () => {
    expect(extractEventTimeLabel({ starts_at_label: "19.06.2026 · 10:15" })).toBe("10:15");
  });

  it("shortens garnet suffix in title", () => {
    expect(shortenFestivalPerformanceTitle("«Пиратские анекдоты» — Бугровский гарнец")).toBe("«Пиратские анекдоты»");
  });
});

describe("isDisplayablePoster", () => {
  it("rejects stock gallery placeholders for cinema", () => {
    expect(isDisplayablePoster("/images/gallery/cinema.jpg", "cinema")).toBe(false);
    expect(isDisplayablePoster("https://cdn.example.com/poster.jpg", "cinema")).toBe(true);
  });
});
