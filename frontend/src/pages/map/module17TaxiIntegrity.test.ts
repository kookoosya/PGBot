import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mapRoot = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(mapRoot, "..", "..", "..", "..");

const REJECTED_TAXI_PHONES = [
  "000-28-28",
  "60-18-18",
  "905-50-50",
  "888-6-777",
  "354-70-24",
];

describe("module 17 taxi integrity", () => {
  it("audit doc records NOT_FOUND scenario", () => {
    const audit = readFileSync(
      join(repoRoot, "docs/factual-integrity/module-17-verified-taxi-contacts.md"),
      "utf8",
    );
    expect(audit).toContain("NOT_FOUND");
    expect(audit).toContain("Work.Taxi");
    expect(audit).toContain("INSUFFICIENT_EVIDENCE");
  });

  it("TAXI_SEED remains empty in backend seed module", () => {
    const seed = readFileSync(
      join(repoRoot, "backend/app/services/pushkin_places_seed.py"),
      "utf8",
    );
    expect(seed).toMatch(/TAXI_SEED:\s*list\[tuple\]\s*=\s*\[\]/);
  });

  it("frontend does not hardcode rejected taxi phones", () => {
    const files = ["TaxiPanel.tsx", "MapServicesTabs.tsx", "verifiedPhoneContacts.ts", "hotlines.ts"];
    for (const file of files) {
      const text = readFileSync(join(mapRoot, file), "utf8");
      for (const phone of REJECTED_TAXI_PHONES) {
        expect(text, `${file} must not contain ${phone}`).not.toContain(phone);
      }
    }
  });

  it("numbers tab still uses verified phone contacts hook from module 16", () => {
    const tabs = readFileSync(join(mapRoot, "MapServicesTabs.tsx"), "utf8");
    expect(tabs).toContain("useVerifiedPhoneContacts");
    expect(tabs).toContain('id: "taxi"');
    expect(tabs).toContain('id: "hotlines"');
  });
});
