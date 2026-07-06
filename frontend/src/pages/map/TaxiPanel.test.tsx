/**
 * @vitest-environment jsdom
 */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TaxiPanel } from "./TaxiPanel";

const sampleTaxi = [
  {
    id: 1,
    name: "Такси Комфорт",
    phone: "+7 (8112) 60-18-18",
    phones_extra: null,
    description: "verified example for test only",
    is_24h: true,
    rating: 4.5,
    price_from: 100,
  },
];

afterEach(() => {
  cleanup();
});

describe("TaxiPanel", () => {
  it("shows empty-state when no verified taxi phones", () => {
    render(<TaxiPanel compact taxi={[]} />);
    expect(screen.getByText("Проверенные номера такси пока не добавлены")).toBeTruthy();
  });

  it("keeps stable empty-state copy for module 17", () => {
    render(<TaxiPanel compact taxi={[]} />);
    expect(screen.getByText("Проверенные номера такси пока не добавлены").textContent).toBe(
      "Проверенные номера такси пока не добавлены",
    );
  });

  it("renders verified taxi cards when API provides them", () => {
    render(<TaxiPanel compact taxi={sampleTaxi} />);
    expect(screen.getByText("Такси Комфорт")).toBeTruthy();
    expect(screen.getByText("+7 (8112) 60-18-18")).toBeTruthy();
  });

  it("does not show empty-state when taxi list is non-empty", () => {
    render(<TaxiPanel compact taxi={sampleTaxi} />);
    expect(screen.queryByText("Проверенные номера такси пока не добавлены")).toBeNull();
  });
});
