import { describe, expect, it } from "vitest";
import { MAP_TILE_OSM, MAP_TILE_SAT, osmTileUrl } from "./mapTiles";

describe("mapTiles", () => {
  it("builds osm tile path", () => {
    expect(osmTileUrl(14, 1234, 5678)).toBe("/tiles/osm/14/1234/5678.png");
  });

  it("exports tile template constants", () => {
    expect(MAP_TILE_OSM).toContain("{z}");
    expect(MAP_TILE_SAT).toContain("{z}");
  });
});
