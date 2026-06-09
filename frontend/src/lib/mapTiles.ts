/** Тайлы карт через наш сервер */
export const MAP_TILE_OSM = "/tiles/osm/{z}/{x}/{y}.png";
export const MAP_TILE_SAT = "/tiles/sat/{z}/{y}/{x}";

export function osmTileUrl(z: number, x: number, y: number): string {
  return `/tiles/osm/${z}/${x}/${y}.png`;
}
