/**
 * @vitest-environment jsdom
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Place } from "@/lib/api/types/places";

import { PlacesList } from "./PlacesList";

const placeWithPhone: Place = {
  id: 326,
  name: "Шиномонтаж",
  category: "tyre",
  category_label: "Шиномонтаж",
  description: null,
  address: "ул. Аэродромная, 23",
  latitude: 57.0173,
  longitude: 28.9335,
  phone: "+7 (906) 221-03-54",
  website: null,
  opening_hours: null,
  avg_rating: 0,
  review_count: 0,
  external_rating: 0,
  external_review_count: 0,
  display_rating: 0,
  display_review_count: 0,
  rating_source: null,
  yandex_url: null,
  complaint_count: 0,
  verification_status: "OWNER_CONFIRMED",
};

describe("PlacesList contact display", () => {
  it("shows verified phone from API in list card", () => {
    render(
      <PlacesList
        places={[placeWithPhone]}
        placesLoading={false}
        placesError={false}
        count={1}
        onOpenPlace={vi.fn()}
        onRetry={vi.fn()}
      />,
    );
    expect(screen.getByText(/\+7 \(906\) 221-03-54/)).toBeTruthy();
  });
});
