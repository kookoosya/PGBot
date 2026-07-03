/**
 * @vitest-environment jsdom
 */
import { describe, expect, it } from "vitest";

import {
  boundsToQueryParams,
  createPlacesRequestController,
  isPlacesAbortError,
  padMapBounds,
  shouldAcceptPlacesResponse,
  type MapBounds,
} from "./mapPlacesRequest";

const VIEWPORT: MapBounds = {
  south: 57.02,
  west: 28.9,
  north: 57.04,
  east: 28.95,
};

describe("mapPlacesRequest", () => {
  it("fail-before: unguarded handler applies stale response", () => {
    let places = [101, 102];
    const applyUnguarded = (items: number[]) => {
      places = items;
    };
    applyUnguarded([201]);
    applyUnguarded([1, 2, 3]);
    expect(places).toEqual([1, 2, 3]);
  });

  it("pass-after: stale response is ignored by request guard", () => {
    let places = [101, 102];
    const latestId = 2;
    const applyGuarded = (responseId: number, items: number[]) => {
      if (shouldAcceptPlacesResponse(responseId, latestId)) {
        places = items;
      }
    };
    applyGuarded(2, [201]);
    applyGuarded(1, [1, 2, 3]);
    expect(places).toEqual([201]);
  });

  it("shouldAcceptPlacesResponse accepts only latest id", () => {
    expect(shouldAcceptPlacesResponse(3, 3)).toBe(true);
    expect(shouldAcceptPlacesResponse(2, 3)).toBe(false);
  });

  it("createPlacesRequestController aborts previous request", () => {
    const controller = createPlacesRequestController();
    const first = controller.start();
    const second = controller.start();
    expect(first.requestId).toBe(1);
    expect(second.requestId).toBe(2);
    expect(first.signal.aborted).toBe(true);
    expect(second.signal.aborted).toBe(false);
    expect(controller.isLatest(1)).toBe(false);
    expect(controller.isLatest(2)).toBe(true);
  });

  it("isPlacesAbortError detects fetch abort", () => {
    expect(isPlacesAbortError(new DOMException("Aborted", "AbortError"))).toBe(true);
    expect(isPlacesAbortError(new Error("HTTP 500"))).toBe(false);
  });

  it("padMapBounds expands viewport without unbounded district load", () => {
    const padded = padMapBounds(VIEWPORT);
    expect(padded.south).toBeLessThan(VIEWPORT.south);
    expect(padded.north).toBeGreaterThan(VIEWPORT.north);
    expect(padded.west).toBeLessThan(VIEWPORT.west);
    expect(padded.east).toBeGreaterThan(VIEWPORT.east);
    const latSpan = VIEWPORT.north - VIEWPORT.south;
    expect(padded.north - padded.south).toBeCloseTo(latSpan * 1.12, 5);
  });

  it("boundsToQueryParams uses padded bounds", () => {
    const params = boundsToQueryParams(VIEWPORT);
    expect(Number(params.south)).toBeLessThan(VIEWPORT.south);
    expect(Number(params.north)).toBeGreaterThan(VIEWPORT.north);
  });

  it("marker near viewport edge stays inside padded query bounds", () => {
    const edgeLat = VIEWPORT.north - 0.0001;
    const edgeLng = VIEWPORT.east - 0.0001;
    const padded = padMapBounds(VIEWPORT);
    expect(edgeLat).toBeLessThanOrEqual(VIEWPORT.north);
    expect(edgeLat).toBeLessThanOrEqual(padded.north);
    expect(edgeLng).toBeLessThanOrEqual(padded.east);
  });
});
