export function yandexRouteUrl(lat: number, lng: number): string {
  return `https://yandex.ru/maps/?rtext=~${lat},${lng}&rtt=auto`;
}

export function yandexMapsPointUrl(lat: number, lng: number, name: string): string {
  return `https://yandex.ru/maps/?pt=${lng},${lat}&z=17&text=${encodeURIComponent(name + " Пушкинские Горы")}`;
}

export function geoNavigateUrl(lat: number, lng: number): string {
  return `geo:${lat},${lng}?q=${lat},${lng}`;
}
