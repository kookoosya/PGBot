/** Map places fetch: stale-response guard and bounds helpers. */

export type MapBounds = {
  south: number;
  west: number;
  north: number;
  east: number;
};

/** Small stable padding so viewport-edge markers stay in query bounds after tiny pans. */
const BBOX_PAD_RATIO = 0.06;

export function padMapBounds(bounds: MapBounds, ratio = BBOX_PAD_RATIO): MapBounds {
  const latSpan = bounds.north - bounds.south;
  const lngSpan = bounds.east - bounds.west;
  const latPad = latSpan * ratio;
  const lngPad = lngSpan * ratio;
  return {
    south: bounds.south - latPad,
    north: bounds.north + latPad,
    west: bounds.west - lngPad,
    east: bounds.east + lngPad,
  };
}

export function shouldAcceptPlacesResponse(responseId: number, latestRequestId: number): boolean {
  return responseId === latestRequestId;
}

export function isPlacesAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export function boundsToQueryParams(bounds: MapBounds): Record<string, string> {
  const padded = padMapBounds(bounds);
  return {
    south: String(padded.south),
    west: String(padded.west),
    north: String(padded.north),
    east: String(padded.east),
  };
}

export type PlacesRequestController = {
  start(): { requestId: number; signal: AbortSignal };
  isLatest(requestId: number): boolean;
};

export function createPlacesRequestController(): PlacesRequestController {
  let latestRequestId = 0;
  let abortController: AbortController | null = null;

  return {
    start() {
      abortController?.abort();
      abortController = new AbortController();
      latestRequestId += 1;
      return { requestId: latestRequestId, signal: abortController.signal };
    },
    isLatest(requestId: number) {
      return shouldAcceptPlacesResponse(requestId, latestRequestId);
    },
  };
}
