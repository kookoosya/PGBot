import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api/index";
import type { Place } from "@/lib/api/types/places";

import { EMERGENCY_HOTLINES } from "./hotlines";
import {
  buildPhoneContactGroups,
  countVerifiedPlacePhones,
  type PhoneContactGroup,
} from "./verifiedPhoneContacts";

export type VerifiedPhoneContactsState = {
  groups: PhoneContactGroup[];
  loading: boolean;
  error: boolean;
  emergencyCount: number;
  verifiedPlaceCount: number;
  totalDisplayCount: number;
};

export function useVerifiedPhoneContacts(): VerifiedPhoneContactsState {
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    api
      .getPlaces({ scope: "VILLAGE", page_size: "500" })
      .then((response) => {
        if (!cancelled) setPlaces(response.items);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const groups = useMemo(() => buildPhoneContactGroups(places), [places]);
  const verifiedPlaceCount = useMemo(() => countVerifiedPlacePhones(places), [places]);
  const emergencyCount = EMERGENCY_HOTLINES.length;

  return {
    groups,
    loading,
    error,
    emergencyCount,
    verifiedPlaceCount,
    totalDisplayCount: emergencyCount + verifiedPlaceCount,
  };
}
