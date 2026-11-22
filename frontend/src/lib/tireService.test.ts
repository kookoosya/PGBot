import { describe, expect, it } from "vitest";
import {
  REMOVAL_INSTALLATION,
  STUDDING,
  TIRE_SERVICE,
  TIRE_SIZE_PRICES,
  TUBE_REPAIR,
  TUBELESS_REPAIR,
  formatRubles,
} from "./tireService";

describe("owner-approved tire price catalog (13.10.2026)", () => {
  it("keeps the published revision and full sizes", () => {
    expect(TIRE_SERVICE.priceRevision).toBe("13.10.2026");
    expect(TIRE_SIZE_PRICES.map((row) => row.size)).toEqual([
      "R12", "R13", "R14", "R15", "R16", "R17", "R18", "R19", "R20",
      "Микроавтобус", "Газель", "УАЗ",
    ]);
  });

  it("preserves package discounts rather than deriving set prices from each wheel", () => {
    expect(TIRE_SIZE_PRICES.find((row) => row.size === "R16")).toMatchObject({
      dismount: 120, mount: 120, balance: 250, wheel: 490, set: 1950, setCount: 4,
    });
    expect(TIRE_SIZE_PRICES.find((row) => row.size === "Газель")).toMatchObject({
      dismount: 160, mount: 160, balance: 250, wheel: 570, set: 3400, setCount: 6,
    });
    expect(TIRE_SIZE_PRICES.find((row) => row.size === "R12")?.set).toBe(1300);
    expect(TIRE_SIZE_PRICES.find((row) => row.size === "R20")?.set).toBe(2450);
  });

  it("contains all priced repair items and does not advertise non-offered work", () => {
    expect(REMOVAL_INSTALLATION).toHaveLength(2);
    expect(TUBELESS_REPAIR).toHaveLength(12);
    expect(TUBE_REPAIR).toHaveLength(6);
    expect(STUDDING).toHaveLength(2);
    const allNames = [
      ...TUBELESS_REPAIR, ...TUBE_REPAIR, ...STUDDING, ...REMOVAL_INSTALLATION,
    ].map((row) => row.name.toLowerCase()).join(" ");
    expect(allNames).not.toMatch(/покраск|прокатк|восстановлени.*диск/);
  });

  it("formats amounts with ruble suffix", () => {
    expect(formatRubles(1950).replace(/\s/g, "")).toBe("1950₽");
  });
});
