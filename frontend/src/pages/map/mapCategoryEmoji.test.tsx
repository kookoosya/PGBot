/**
 * @vitest-environment jsdom
 */
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CATEGORY_ICONS } from "./constants";
import { makeIcon } from "./icons";
import { LEAFLET_ATTRIBUTION_PREFIX, LEAFLET_FLAG_MARKERS, applyLeafletAttributionPrefix } from "./mapAttribution";
import { MapMoreCategories } from "./MapMoreCategories";
import { MapStatsRibbon } from "./MapStatsRibbon";
import { PlaceDetailPanel } from "./PlaceDetailPanel";
import { PlacesList } from "./PlacesList";

const REQUIRED_EMOJI: Record<string, string> = {
  shop: "🛒",
  supermarket: "🏪",
  pharmacy: "💊",
  school: "🏫",
  hospital: "🏥",
  vet: "🐾",
  hotel: "🏨",
  tyre: "🛞",
  auto: "🔧",
  car_wash: "🧽",
  auto_parts: "⚙️",
  towing: "🚚",
};

const sampleStats = {
  total_places: 12,
  by_category: {
    supermarket: 3,
    hotel: 2,
    hospital: 1,
    pharmacy: 2,
    vet: 1,
  },
  last_sync: "2026-06-27T12:00:00Z",
  center: { lat: 57.0267, lng: 28.91 },
};

const samplePlace = {
  id: 1,
  name: "Тестовая аптека",
  category: "pharmacy",
  category_label: "Аптека",
  address: "ул. Ленина",
  latitude: 57.02,
  longitude: 28.91,
  display_rating: 4.5,
  display_review_count: 2,
  phone: "+7",
};

const panelProps = {
  selected: {
    ...samplePlace,
    description: "",
    hours: "",
    website: "",
    reviews: [],
    complaints: [],
    reports: [],
    is_reference: false,
    source: "osm",
    yandex_id: null,
    display_rating: 4.5,
    display_review_count: 2,
  },
  tab: "info" as const,
  setTab: vi.fn(),
  msg: "",
  msgType: "info" as const,
  reviewForm: { rating: 5, text: "" },
  setReviewForm: vi.fn(),
  complaintForm: { type: "", text: "" },
  setComplaintForm: vi.fn(),
  reportForm: { type: "", text: "" },
  setReportForm: vi.fn(),
  complaintTypes: [],
  mapReportTypes: [],
  submitReview: vi.fn(),
  submitComplaint: vi.fn(),
  submitReport: vi.fn(),
  clearSelection: vi.fn(),
};

vi.mock("react-leaflet", async () => {
  const actual = await vi.importActual<typeof import("react-leaflet")>("react-leaflet");
  return {
    ...actual,
    useMapEvents: () => ({}),
  };
});

describe("CATEGORY_ICONS", () => {
  it("contains emoji for all current categories", () => {
    for (const [slug, emoji] of Object.entries(CATEGORY_ICONS)) {
      expect(emoji.length).toBeGreaterThan(0);
      expect(slug).toBeTruthy();
    }
    for (const [slug, emoji] of Object.entries(REQUIRED_EMOJI)) {
      expect(CATEGORY_ICONS[slug]).toBe(emoji);
    }
  });

  it("uses 🐾 for vet and differs from hospital 🏥", () => {
    expect(CATEGORY_ICONS.vet).toBe("🐾");
    expect(CATEGORY_ICONS.hospital).toBe("🏥");
    expect(CATEGORY_ICONS.vet).not.toBe(CATEGORY_ICONS.hospital);
  });

  it("falls back to 📍 for unknown categories", () => {
    expect(CATEGORY_ICONS["unknown-category"]).toBeUndefined();
    expect(CATEGORY_ICONS.other).toBe("📍");
    expect(makeIcon("unknown-category", 0, false).options.html).toContain("📍");
  });
});

describe("MapStatsRibbon", () => {
  it("shows category emoji in ribbon rows", () => {
    const { container } = render(
      <MapStatsRibbon
        stats={sampleStats}
        categories={[
          { value: "supermarket", label: "Супермаркет" },
          { value: "hotel", label: "Гостиница" },
          { value: "vet", label: "Ветеринария" },
        ]}
        activeCategory=""
        onCategoryClick={() => {}}
      />,
    );
    expect(container.textContent).toContain("🏪");
    expect(container.textContent).toContain("🏨");
    expect(container.textContent).toContain("🐾");
  });

  it("keeps category filters clickable", () => {
    const onCategoryClick = vi.fn();
    render(
      <MapStatsRibbon
        stats={{ ...sampleStats, by_category: { supermarket: 2 } }}
        categories={[{ value: "supermarket", label: "Супермаркет" }]}
        activeCategory=""
        onCategoryClick={onCategoryClick}
      />,
    );
    fireEvent.click(screen.getByTitle("Супермаркет: 2"));
    expect(onCategoryClick).toHaveBeenCalledWith("supermarket");
  });
});

describe("Leaflet marker icons", () => {
  it("embeds category emoji in marker HTML", () => {
    const html = String(makeIcon("supermarket", 4.6, true).options.html);
    expect(html).toContain("🏪");
    expect(html).toContain("map-marker-emoji");
    expect(html).not.toContain("map-marker-icon");
  });
});

describe("PlacesList", () => {
  it("shows category emoji in list rows", () => {
    const { container } = render(
      <PlacesList
        places={[samplePlace]}
        placesLoading={false}
        placesError={false}
        onOpenPlace={() => {}}
        onRetry={() => {}}
      />,
    );
    expect(container.querySelector(".org-list-icon")?.textContent).toBe("💊");
  });
});

describe("PlaceDetailPanel", () => {
  it("shows category emoji in detail header", () => {
    const { container } = render(<PlaceDetailPanel {...panelProps} />);
    expect(container.querySelector(".org-detail-icon")?.textContent).toBe("💊");
  });
});

describe("MapMoreCategories", () => {
  it("shows category emoji in more-categories chips", () => {
    render(
      <MapMoreCategories
        topCategories={["supermarket"]}
        categories={[
          { value: "supermarket", label: "Супермаркет" },
          { value: "tyre", label: "Шиномонтаж" },
        ]}
        activeCategory=""
        onSelect={() => {}}
      />,
    );
    expect(screen.getByText(/🛞/)).toBeTruthy();
  });
});

describe("Leaflet attribution prefix", () => {
  it("contains Leaflet link text without flag markers", () => {
    expect(LEAFLET_ATTRIBUTION_PREFIX).toContain("Leaflet");
    expect(LEAFLET_ATTRIBUTION_PREFIX).toContain("https://leafletjs.com");
    for (const marker of LEAFLET_FLAG_MARKERS) {
      expect(LEAFLET_ATTRIBUTION_PREFIX).not.toContain(marker);
    }
  });

  it("applies prefix without flag markers", () => {
    const setPrefix = vi.fn();
    applyLeafletAttributionPrefix({ attributionControl: { setPrefix } });
    expect(setPrefix).toHaveBeenCalledWith(LEAFLET_ATTRIBUTION_PREFIX);
    for (const marker of LEAFLET_FLAG_MARKERS) {
      expect(setPrefix.mock.calls[0][0]).not.toContain(marker);
    }
  });
});

describe("OpenStreetMap attribution", () => {
  it("preserves OSM text in TileLayer attribution string", () => {
    const schemeAttribution = "© OpenStreetMap · справочник посёлка";
    expect(schemeAttribution).toContain("© OpenStreetMap");
    expect(schemeAttribution).toContain("справочник посёлка");
    for (const marker of LEAFLET_FLAG_MARKERS) {
      expect(schemeAttribution).not.toContain(marker);
    }
  });
});
