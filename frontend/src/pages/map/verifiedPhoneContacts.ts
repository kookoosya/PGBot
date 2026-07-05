import type { Place } from "@/lib/api/types/places";

import { CATEGORY_ICONS } from "./constants";
import { EMERGENCY_HOTLINES } from "./hotlines";

export type PhoneContactEntry = {
  id: string;
  icon: string;
  name: string;
  phone: string;
  category: string;
  category_label: string;
  address?: string | null;
  note?: string | null;
  website?: string | null;
  verification_label?: string | null;
};

export type PhoneContactGroup = {
  title: string;
  items: PhoneContactEntry[];
};

const PHONE_GROUP_DEFS: { title: string; categories: string[] }[] = [
  { title: "Медицина и аптеки", categories: ["pharmacy", "hospital", "vet"] },
  { title: "Госуслуги и учреждения", categories: ["government", "post", "bank", "school"] },
  { title: "Такси и транспорт", categories: ["taxi", "transport"] },
  { title: "Еда и гостиницы", categories: ["cafe", "restaurant", "hotel"] },
  { title: "Авто", categories: ["auto", "car_wash", "auto_parts", "tyre", "gas"] },
  { title: "Культура и туризм", categories: ["culture", "parking"] },
  { title: "Прочее", categories: ["supermarket", "shop", "beauty", "library", "other"] },
];

export function normalizePhoneKey(phone: string): string {
  return phone.replace(/\D/g, "");
}

export function placesWithVerifiedPhones(places: Place[]): Place[] {
  return places.filter((p) => {
    if (!p.phone?.trim()) return false;
    if (p.scope && p.scope !== "VILLAGE") return false;
    return true;
  });
}

function contactNote(place: Place): string | null {
  const parts: string[] = [];
  if (place.address) parts.push(place.address);
  if (place.verification_label) parts.push(place.verification_label);
  return parts.length ? parts.join(" · ") : null;
}

export function buildPhoneContactGroups(places: Place[]): PhoneContactGroup[] {
  const seen = new Set<string>();
  for (const entry of EMERGENCY_HOTLINES) {
    seen.add(normalizePhoneKey(entry.phone));
  }

  const entries: PhoneContactEntry[] = [];
  for (const place of placesWithVerifiedPhones(places)) {
    const phone = place.phone!.trim();
    const key = normalizePhoneKey(phone);
    if (seen.has(key)) continue;
    seen.add(key);
    entries.push({
      id: `place-${place.id}`,
      icon: CATEGORY_ICONS[place.category] || "📍",
      name: place.name,
      phone,
      category: place.category,
      category_label: place.category_label,
      address: place.address,
      note: contactNote(place),
      website: place.website,
      verification_label: place.verification_label,
    });
  }

  const assigned = new Set<string>();
  const groups: PhoneContactGroup[] = [];

  for (const def of PHONE_GROUP_DEFS) {
    const items = entries.filter(
      (entry) => !assigned.has(entry.id) && def.categories.includes(entry.category),
    );
    for (const item of items) assigned.add(item.id);
    if (items.length > 0) groups.push({ title: def.title, items });
  }

  const rest = entries.filter((entry) => !assigned.has(entry.id));
  if (rest.length > 0) {
    const other = groups.find((group) => group.title === "Прочее");
    if (other) other.items.push(...rest);
    else groups.push({ title: "Прочее", items: rest });
  }

  return groups;
}

export function countVerifiedPlacePhones(places: Place[]): number {
  return buildPhoneContactGroups(places).reduce((sum, group) => sum + group.items.length, 0);
}
