import { describe, expect, it } from "vitest";
import {
  boardApiParams,
  boardFromPath,
  boardPathForCategory,
  categoriesForBoard,
} from "./classifiedBoard";

describe("classifiedBoard", () => {
  it("resolves board from path", () => {
    expect(boardFromPath("/classifieds")).toBe("all");
    expect(boardFromPath("/classifieds/sale")).toBe("sale");
    expect(boardFromPath("/classifieds/services")).toBe("services");
    expect(boardFromPath("/classifieds/help")).toBe("help");
  });

  it("maps API params per board", () => {
    expect(boardApiParams("sale")).toEqual({ market_only: "true" });
    expect(boardApiParams("services")).toEqual({ services_only: "true" });
    expect(boardApiParams("help")).toEqual({ neighbor_only: "true" });
    expect(boardApiParams("all")).toEqual({ ads_only: "true" });
  });

  it("back path from category", () => {
    expect(boardPathForCategory("sale")).toBe("/classifieds/sale");
    expect(boardPathForCategory("neighbor_help")).toBe("/classifieds/help");
    expect(boardPathForCategory("firewood")).toBe("/classifieds/services");
  });

  it("filters categories per board", () => {
    const all = [
      { value: "sale", label: "Продажа" },
      { value: "firewood", label: "Дрова" },
      { value: "neighbor_help", label: "Сосед" },
      { value: "job_tourism", label: "Туризм" },
    ];
    expect(categoriesForBoard("sale", all).map((c) => c.value)).toEqual(["sale"]);
    expect(categoriesForBoard("help", all).map((c) => c.value)).toEqual(["neighbor_help"]);
    expect(categoriesForBoard("all", all).map((c) => c.value)).toEqual(["sale", "firewood"]);
  });
});
