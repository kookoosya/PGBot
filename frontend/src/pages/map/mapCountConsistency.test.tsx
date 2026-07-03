/**
 * @vitest-environment jsdom
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MapMoreCategories } from "./MapMoreCategories";
import {
  MapStatsRibbon,
  hiddenCategoryTotal,
  sumCategoryCounts,
  topCategoryEntries,
} from "./MapStatsRibbon";
import { PlacesList } from "./PlacesList";

const byCategory = {
  supermarket: 8,
  pharmacy: 6,
  auto: 5,
  hospital: 4,
  vet: 3,
  gas: 3,
  cafe: 3,
  school: 2,
  tyre: 2,
  post: 2,
  bank: 2,
  beauty: 1,
  towing: 1,
  car_wash: 1,
  auto_parts: 1,
  parking: 1,
};

const stats = {
  total_places: 45,
  catalog_places: 45,
  mappable_places: 45,
  by_category: byCategory,
  last_sync: "2026-07-03T12:00:00Z",
  center: { lat: 57.03, lng: 28.92 },
  reference_places: 40,
};

describe("map count helpers", () => {
  it("sums all category counts", () => {
    expect(sumCategoryCounts(byCategory)).toBe(45);
  });

  it("computes hidden total beyond top 8", () => {
    const top8 = topCategoryEntries(byCategory).reduce((s, [, n]) => s + n, 0);
    expect(top8).toBe(34);
    expect(hiddenCategoryTotal(byCategory)).toBe(11);
  });
});

describe("MapStatsRibbon count semantics", () => {
  it("does not label global total as places on map", () => {
    const { container } = render(
      <MapStatsRibbon
        stats={stats}
        categories={[]}
        activeCategory=""
        onCategoryClick={() => {}}
        currentAreaCount={12}
      />,
    );
    expect(container.textContent).toContain("Всего в справочнике: 45");
    expect(container.textContent).toContain("В видимой области: 12");
    expect(container.textContent).not.toMatch(/45\s+мест на карте/);
  });

  it("shows mappable line only when it differs from catalog", () => {
    const { container, rerender } = render(
      <MapStatsRibbon
        stats={{ ...stats, mappable_places: 43 }}
        categories={[]}
        activeCategory=""
        onCategoryClick={() => {}}
        currentAreaCount={10}
      />,
    );
    expect(container.textContent).toContain("С координатами на карте: 43");
    rerender(
      <MapStatsRibbon
        stats={stats}
        categories={[]}
        activeCategory=""
        onCategoryClick={() => {}}
        currentAreaCount={10}
      />,
    );
    expect(container.textContent).not.toContain("С координатами на карте");
  });

  it("shows hidden category subtotal when more than 8 categories", () => {
    const { container } = render(
      <MapStatsRibbon
        stats={stats}
        categories={[]}
        activeCategory=""
        onCategoryClick={() => {}}
        currentAreaCount={null}
      />,
    );
    expect(container.textContent).toContain("Остальные категории: 11");
  });

  it("uses filter label for current area when filter active", () => {
    const { container } = render(
      <MapStatsRibbon
        stats={stats}
        categories={[]}
        activeCategory="pharmacy"
        onCategoryClick={() => {}}
        currentAreaCount={4}
        hasActiveFilter
      />,
    );
    expect(container.textContent).toContain("По фильтру в видимой области: 4");
  });

  it("shows updating message during incompatible filter loading", () => {
    const { container } = render(
      <MapStatsRibbon
        stats={stats}
        categories={[]}
        activeCategory="pharmacy"
        onCategoryClick={() => {}}
        currentAreaCount={null}
        hasActiveFilter
        incompatibleFilterLoading
      />,
    );
    expect(container.textContent).toContain("Обновляем список…");
    expect(container.textContent).not.toContain("По фильтру в видимой области:");
  });
});

describe("MapMoreCategories counts", () => {
  it("shows subtotal for remaining categories", () => {
    const top = topCategoryEntries(byCategory).map(([cat]) => cat);
    render(
      <MapMoreCategories
        topCategories={top}
        categories={Object.keys(byCategory).map((value) => ({ value, label: value }))}
        activeCategory=""
        onSelect={() => {}}
        categoryCounts={byCategory}
      />,
    );
    expect(screen.getByText(/Ещё категории \(8 · 11 организаций\)/)).toBeTruthy();
  });
});

describe("PlacesList count display", () => {
  it("shows current area count from response total", () => {
    const { container } = render(
      <PlacesList
        places={[]}
        placesLoading={false}
        placesError={false}
        count={12}
        onOpenPlace={() => {}}
        onRetry={() => {}}
      />,
    );
    expect(container.textContent).toContain("В видимой области: 12");
  });

  it("renders stable data-place-id on each row", () => {
    const { container } = render(
      <PlacesList
        places={[{ id: 42, name: "A", category: "pharmacy", category_label: "Аптека", address: "", latitude: 1, longitude: 1, display_rating: 0, display_review_count: 0, phone: null }]}
        placesLoading={false}
        placesError={false}
        count={1}
        onOpenPlace={() => {}}
        onRetry={() => {}}
      />,
    );
    expect(container.querySelector('[data-place-id="42"]')).toBeTruthy();
  });

  it("shows incompatible filter loading state", () => {
    const { container } = render(
      <PlacesList
        places={[]}
        placesLoading
        placesError={false}
        count={null}
        incompatibleFilterLoading
        onOpenPlace={() => {}}
        onRetry={() => {}}
      />,
    );
    expect(within(container).getByText("Обновляем список…")).toBeTruthy();
  });

  it("keeps count visible while bbox loading when prior rows exist", () => {
    const { container } = render(
      <PlacesList
        places={[{ id: 1, name: "A", category: "pharmacy", category_label: "Аптека", address: "", latitude: 1, longitude: 1, display_rating: 0, display_review_count: 0, phone: null }]}
        placesLoading
        placesError={false}
        count={12}
        onOpenPlace={() => {}}
        onRetry={() => {}}
      />,
    );
    expect(container.textContent).toContain("В видимой области: 12");
    expect(container.textContent).toContain("обновляем");
  });
});
