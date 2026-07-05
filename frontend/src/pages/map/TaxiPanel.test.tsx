/**
 * @vitest-environment jsdom
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TaxiPanel } from "./TaxiPanel";

describe("TaxiPanel", () => {
  it("shows empty-state when no verified taxi phones", () => {
    render(<TaxiPanel compact taxi={[]} />);
    expect(screen.getByText("Проверенные номера такси пока не добавлены")).toBeTruthy();
  });
});
