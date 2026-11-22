/** Prices from owner-provided document "ШИНОМОНТАЖ ПУШКИНСКИЕ ГОРЫ", revision 13.10.2026.
 * Do not infer totals: the published set prices differ from per-wheel × quantity.
 * Wheel removal/installation is charged separately from tire mounting.
 */
export const TIRE_SERVICE = {
  name: "Шиномонтаж",
  locality: "Пушкинские Горы",
  address: "Псковская область, рп. Пушкинские Горы, ул. Аэродромная, 23",
  phoneDisplay: "+7 (906) 221-03-54",
  phoneHref: "tel:+79062210354",
  yandexMapsUrl: "https://yandex.ru/maps/org/shinomontazh/1703652438/",
  // Destination from the verified place inventory (shinomontazh-aerodromnaya-23).
  yandexRouteUrl: "https://yandex.ru/maps/?rtext=~57.017306%2C28.933486&rtt=auto",
  priceRevision: "13.10.2026",
  materials: "ROSSVIK",
} as const;

export type TireSizePrice = {
  size: string;
  dismount: number;
  mount: number;
  balance: number;
  wheel: number;
  set: number;
  setCount: number;
};

export const TIRE_SIZE_PRICES: readonly TireSizePrice[] = [
  { size: "R12", dismount: 80, mount: 80, balance: 170, wheel: 330, set: 1300, setCount: 4 },
  { size: "R13", dismount: 90, mount: 90, balance: 220, wheel: 400, set: 1600, setCount: 4 },
  { size: "R14", dismount: 100, mount: 100, balance: 240, wheel: 440, set: 1750, setCount: 4 },
  { size: "R15", dismount: 110, mount: 110, balance: 250, wheel: 470, set: 1850, setCount: 4 },
  { size: "R16", dismount: 120, mount: 120, balance: 250, wheel: 490, set: 1950, setCount: 4 },
  { size: "R17", dismount: 130, mount: 130, balance: 260, wheel: 520, set: 2050, setCount: 4 },
  { size: "R18", dismount: 140, mount: 140, balance: 290, wheel: 570, set: 2250, setCount: 4 },
  { size: "R19", dismount: 150, mount: 150, balance: 290, wheel: 590, set: 2350, setCount: 4 },
  { size: "R20", dismount: 160, mount: 160, balance: 300, wheel: 620, set: 2450, setCount: 4 },
  { size: "Микроавтобус", dismount: 170, mount: 170, balance: 210, wheel: 550, set: 2200, setCount: 4 },
  { size: "Газель", dismount: 160, mount: 160, balance: 250, wheel: 570, set: 3400, setCount: 6 },
  { size: "УАЗ", dismount: 200, mount: 200, balance: 250, wheel: 650, set: 2600, setCount: 4 },
];

export const REMOVAL_INSTALLATION = [
  { name: "Легковой автомобиль", price: "100 ₽" },
  { name: "Микроавтобус / УАЗ / джип / Газель", price: "150 ₽" },
] as const;

export type ServicePrice = { name: string; price: string };

export const TUBELESS_REPAIR: readonly ServicePrice[] = [
  { name: "Ремонт прокола жгутом", price: "250 ₽" },
  { name: "Ремонт пореза кордовым пластырем", price: "550–2 200 ₽" },
  { name: "Ремонт прокола грибком", price: "500–1 650 ₽" },
  { name: "Герметик при сборке колеса", price: "100 ₽" },
  { name: "Герметик на собранном колесе", price: "250 ₽" },
  { name: "Установка вентиля при шиномонтаже", price: "50 ₽" },
  { name: "Замена вентиля на собранном колесе", price: "250 ₽" },
  { name: "Проверка колеса на герметичность", price: "50 ₽" },
  { name: "Чистка диска от ржавчины", price: "100 ₽" },
  { name: "Зачистка бортов диска болгаркой", price: "100 ₽" },
  { name: "При зачистке: герметик / вентиль", price: "+50 ₽ / +50 ₽" },
  { name: "Вулканизация", price: "900–2 750 ₽" },
];

export const TUBE_REPAIR: readonly ServicePrice[] = [
  { name: "Ремонт прокола легковой камеры", price: "200 ₽" },
  { name: "Ремонт прокола грузовой камеры", price: "250 ₽" },
  { name: "Ремонт пореза до 1 см", price: "220 ₽" },
  { name: "Каждый следующий см пореза", price: "60 ₽" },
  { name: "Вклейка вентиля — легковая камера", price: "550 ₽" },
  { name: "Вклейка вентиля — трактор / ГАЗОН", price: "1 600 ₽" },
];

export const STUDDING: readonly ServicePrice[] = [
  { name: "Установка ремонтного шипа (1 шт., с материалом)", price: "15 ₽" },
  { name: "Удаление старого шипа (1 шт.)", price: "5 ₽" },
];

export const ROSSVIK_VIDEOS = [
  {
    title: "Ремонт бескамерной шины жгутами",
    url: "https://rutube.ru/video/c6173d6d474e3599ba2a7914aeeb4a0b/",
    source: "Группа компаний ROSSVIK",
    service: "Ремонт прокола",
  },
  {
    title: "Шиноремонт с помощью грибка — обучение",
    url: "https://rossvik-shop.ru/press/videogallery/ekspertnye-video/remont-shin-gribkom-obuchenie/",
    source: "ROSSVIK",
    service: "Ремонт грибком",
  },
  {
    title: "Экспертные видео: дошиповка и ремонт шин",
    url: "https://rossvik-shop.ru/press/videogallery/ekspertnye-video/",
    source: "ROSSVIK",
    service: "Дошиповка",
  },
] as const;

export function formatRubles(value: number): string {
  return `${value.toLocaleString("ru-RU")} ₽`;
}

/** The published complete-set amount takes precedence over per-wheel arithmetic. */
export function estimateMounting(size: string, count: number) {
  const tariff = TIRE_SIZE_PRICES.find((item) => item.size === size);
  if (!tariff || !Number.isInteger(count) || count < 1 || count > 6) {
    throw new RangeError("Выберите размер из прайса и от 1 до 6 колёс");
  }
  const usesSetPrice = count === tariff.setCount;
  return { amount: usesSetPrice ? tariff.set : tariff.wheel * count, usesSetPrice };
}
