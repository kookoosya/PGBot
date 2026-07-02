/**
 * @vitest-environment jsdom
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  CATEGORY_ICON_COMPONENTS,
  CategoryIcon,
  PLACE_CATEGORY_SLUGS,
  getCategoryIconComponent,
} from "./categoryIcons";
import { makeIcon } from "./icons";
import { MapStatsRibbon } from "./MapStatsRibbon";

const FORBIDDEN_EMOJI = ["🏪", "🏨", "🏫", "🏥", "🇺🇦", "🇷🇺", "📍", "🛒", "💊"];

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

describe("categoryIcons", () => {
  it("maps every PlaceCategory slug to a Lucide component", () => {
    for (const slug of PLACE_CATEGORY_SLUGS) {
      expect(CATEGORY_ICON_COMPONENTS[slug]).toBeTruthy();
    }
  });

  it("uses PawPrint for vet, not Hospital", () => {
    expect(getCategoryIconComponent("vet")).not.toBe(CATEGORY_ICON_COMPONENTS.hospital);
    expect(getCategoryIconComponent("vet")).toBe(CATEGORY_ICON_COMPONENTS.vet);
  });

  it("falls back to MapPin for unknown categories", () => {
    expect(getCategoryIconComponent("unknown-category")).toBe(CATEGORY_ICON_COMPONENTS.other);
  });

  it("renders decorative CategoryIcon with aria-hidden", () => {
    const { container } = render(<CategoryIcon category="supermarket" className="map-category-icon" />);
    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
    expect(svg?.getAttribute("aria-hidden")).toBe("true");
  });
});

describe("MapStatsRibbon category icons", () => {
  it("does not render Unicode emoji in category rows", () => {
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

    const html = container.innerHTML;
    for (const emoji of FORBIDDEN_EMOJI) {
      expect(html).not.toContain(emoji);
    }
    expect(container.querySelectorAll("svg").length).toBeGreaterThanOrEqual(3);
  });

  it("keeps visible category labels as text", () => {
    render(
      <MapStatsRibbon
        stats={sampleStats}
        categories={[
          { value: "supermarket", label: "Супермаркет" },
          { value: "hotel", label: "Гостиница" },
        ]}
        activeCategory=""
        onCategoryClick={() => {}}
      />,
    );

    expect(screen.getAllByText("Супермаркет").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Гостиница").length).toBeGreaterThan(0);
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);
  });

  it("renders hotel and supermarket as SVG icons", () => {
    const { container } = render(
      <MapStatsRibbon
        stats={{ ...sampleStats, by_category: { supermarket: 2, hotel: 1 } }}
        categories={[
          { value: "supermarket", label: "Супермаркет" },
          { value: "hotel", label: "Гостиница" },
        ]}
        activeCategory=""
        onCategoryClick={() => {}}
      />,
    );

    expect(container.querySelectorAll("svg.map-category-icon").length).toBe(2);
  });
});

describe("Leaflet marker icons", () => {
  it("embeds static SVG markup in marker HTML", () => {
    const icon = makeIcon("supermarket", 4.6, true);
    const html = String(icon.options.html);
    expect(html).toContain("<svg");
    expect(html).toContain("map-marker-icon");
    expect(html).not.toContain("map-marker-emoji");
  });

  it("does not embed forbidden emoji in marker HTML", () => {
    for (const category of ["supermarket", "hotel", "school", "hospital", "vet"]) {
      const html = String(makeIcon(category, 0, false).options.html);
      for (const emoji of FORBIDDEN_EMOJI) {
        expect(html).not.toContain(emoji);
      }
    }
  });

  it("uses MapPin markup for unknown categories", () => {
    const html = String(makeIcon("unknown-category", 0, false).options.html);
    expect(html).toContain("<svg");
    expect(html).toContain('aria-hidden="true"');
  });
});
