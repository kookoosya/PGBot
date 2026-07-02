import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const pagesRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = join(pagesRoot, "..", "..", "..");

const PUBLIC_MAP_UI_FILES = [
  join(pagesRoot, "Map.tsx"),
  join(pagesRoot, "map/PlacesList.tsx"),
  join(pagesRoot, "map/MapStatsRibbon.tsx"),
  join(pagesRoot, "map/PlaceDetailPanel.tsx"),
  join(pagesRoot, "map/hotlines.ts"),
  join(pagesRoot, "map/HotlinesPanel.tsx"),
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

const FORBIDDEN_PHONES = [
  "2-01-01",
  "2-02-02",
  "2-05-05",
  "2-06-06",
  "000-28-28",
  "997-90-00",
];

const OLD_MONASTERY_NAME = "Свято-Успенская Пушкиногорская лавра";
const OFFICIAL_MONASTERY_NAME = "Свято-Успенский Святогорский мужской монастырь";

describe("map factual integrity UI (stage 1)", () => {
  for (const filePath of PUBLIC_MAP_UI_FILES) {
    const rel = filePath.replace(repoRoot + "/", "").replace(/\\/g, "/");

    it(`does not claim verified reference semantics in ${rel}`, () => {
      const text = readFileSync(filePath, "utf8");
      for (const phrase of FORBIDDEN_PHRASES) {
        expect(text, `forbidden phrase: ${phrase}`).not.toContain(phrase);
      }
    });

    it(`does not expose placeholder phones in ${rel}`, () => {
      const text = readFileSync(filePath, "utf8");
      for (const phone of FORBIDDEN_PHONES) {
        expect(text, `placeholder phone: ${phone}`).not.toContain(phone);
      }
    });

    it(`does not use deprecated monastery name in ${rel}`, () => {
      const text = readFileSync(filePath, "utf8");
      expect(text).not.toContain(OLD_MONASTERY_NAME);
    });
  }

  it("hotlines lists official monastery contact when monastery is shown", () => {
    const text = readFileSync(join(pagesRoot, "map/hotlines.ts"), "utf8");
    expect(text).toContain(OFFICIAL_MONASTERY_NAME);
  });

  it("hotlines does not mention 911", () => {
    const text = readFileSync(join(pagesRoot, "map/hotlines.ts"), "utf8");
    expect(text).not.toContain("911");
  });
});
