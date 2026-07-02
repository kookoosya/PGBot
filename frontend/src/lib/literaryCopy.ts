/** Тексты интерфейса портала — единый деловой тон */

import {
  LANDING_HERO_COPY,
  LANDING_SECTIONS_COPY,
  PAGE_SECTIONS_COPY,
  PORTAL_COPY_BRAND,
} from "./portalCopyShared";

export { ISSUE_STATUS_HINTS, EMPTY_STATES } from "./portalCopyShared";

export const LANDING_HERO = {
  kicker: PORTAL_COPY_BRAND.kicker,
  tagline: PORTAL_COPY_BRAND.tagline,
  quote: LANDING_HERO_COPY.quote,
  quoteSource: LANDING_HERO_COPY.quote_source,
  quoteWork: (LANDING_HERO_COPY as { quote_work?: string }).quote_work,
  quoteYear: (LANDING_HERO_COPY as { quote_year?: number }).quote_year,
  lead: LANDING_HERO_COPY.lead,
  ctaMap: LANDING_HERO_COPY.cta_map,
  ctaEvents: LANDING_HERO_COPY.cta_events,
  ctaClassifieds: LANDING_HERO_COPY.cta_classifieds,
} as const;

export const PAGE_SECTIONS = PAGE_SECTIONS_COPY;
export const LANDING_SECTIONS = LANDING_SECTIONS_COPY;
