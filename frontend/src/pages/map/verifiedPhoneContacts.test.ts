import { describe, expect, it } from "vitest";

import type { Place } from "@/lib/api/types/places";

import {
  buildPhoneContactGroups,
  countVerifiedPlacePhones,
  normalizePhoneKey,
  placesWithVerifiedPhones,
} from "./verifiedPhoneContacts";

const samplePlace = (overrides: Partial<Place> & Pick<Place, "id" | "name" | "category">): Place => ({
  category_label: overrides.category,
  description: null,
  address: null,
  latitude: 57.02,
  longitude: 28.91,
  phone: null,
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
  scope: "VILLAGE",
  ...overrides,
});

describe("verifiedPhoneContacts", () => {
  it("includes only village places with phone", () => {
    const places = [
      samplePlace({ id: 1, name: "A", category: "pharmacy", phone: "+7 (8112) 60-77-11" }),
      samplePlace({ id: 2, name: "B", category: "cafe", phone: null }),
      samplePlace({ id: 3, name: "C", category: "hotel", phone: "+7 (800) 000-00-00", scope: "NEARBY_ATTRACTION" }),
    ];
    expect(placesWithVerifiedPhones(places)).toHaveLength(1);
  });

  it("groups pharmacy and hospital contacts", () => {
    const places = [
      samplePlace({ id: 10, name: "Аптека-А", category: "pharmacy", phone: "+7 (8112) 60-77-11" }),
      samplePlace({ id: 11, name: "Больница", category: "hospital", phone: "+7 (81146) 2-27-06" }),
    ];
    const groups = buildPhoneContactGroups(places);
    expect(groups[0]?.title).toBe("Медицина и аптеки");
    expect(groups[0]?.items).toHaveLength(2);
  });

  it("deduplicates shared phone numbers", () => {
    const places = [
      samplePlace({ id: 20, name: "Музей", category: "culture", phone: "+7 (81146) 2-23-21" }),
      samplePlace({ id: 21, name: "НКЦ", category: "culture", phone: "+7 (81146) 2-23-21" }),
    ];
    expect(countVerifiedPlacePhones(places)).toBe(1);
  });

  it("normalizes phone keys for dedupe", () => {
    const key = normalizePhoneKey("+7 (906) 221-03-54");
    expect(key).toBe("79062210354");
    expect(key).toBe(normalizePhoneKey("7 (906) 221-03-54"));
  });
});
