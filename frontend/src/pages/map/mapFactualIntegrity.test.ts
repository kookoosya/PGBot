import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

const MAP_UI_FILES = [
  "src/pages/Map.tsx",
  "src/pages/map/PlacesList.tsx",
  "src/pages/map/MapStatsRibbon.tsx",
  "src/pages/map/PlaceDetailPanel.tsx",
];

const FORBIDDEN_PHRASES = [
  "Проверенный справочник",
  "проверены вручную",
  "проверенных",
  "проверенные точки отмечены",
  "проверены справочником",
  "org-list-ref",
  "map-ref-badge",
  'rating_source === "reference"',
];

describe("map factual integrity UI (stage 1)", () => {
  for (const rel of MAP_UI_FILES) {
    it(`does not claim verified reference semantics in ${rel}`, () => {
      const text = readFileSync(join(root, rel), "utf8");
      for (const phrase of FORBIDDEN_PHRASES) {
        expect(text, `forbidden phrase: ${phrase}`).not.toContain(phrase);
      }
    });
  }
});
