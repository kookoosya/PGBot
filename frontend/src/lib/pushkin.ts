export const PUSHKIN_QUOTES: Record<string, string> = {
  home: "«Любви, надежды, тихой славы\nНедолго сердцу снабжать...»",
  ai: "«Счастье то, что дух просветляет.»",
  map: "«Здесь русский дух... здесь Русью пахнет!»",
  services: "«Труд — вот лучшая зарядка для юности!»",
  classifieds: "«Всё, что ни делается, — к лучшему.»",
  register: "«Береги минуту — час сбережёшь.»",
  default: "«Я памятник себе воздвиг нерукотворный...»",
};

export const PUSHKIN_VERSES = [
  "«Уж небо осенью дышало...»",
  "«Здесь русский дух... здесь Русью пахнет!»",
  "«Труд — вот лучшая зарядка для юности!»",
  "«Всё, что ни делается, — к лучшему.»",
];

export const SITE_URL = "https://pushkiny.gmxreply.com";

/** Фото Пушкиногорья — локальные копии с Wikimedia Commons */
export const VILLAGE_PHOTOS = [
  {
    title: "Михайловское",
    caption: "Усадьба музея-заповедника А.С. Пушкина",
    url: "/images/gallery/mikhailovskoe.jpg",
    webp: "/images/gallery/mikhailovskoe.webp",
    credit: "Wikimedia / Alexey Komarov, 2018",
  },
  {
    title: "Святогорский монастырь",
    caption: "Пушкиногорская лавра над рекой Сороть",
    url: "/images/gallery/monastery.jpg",
    webp: "/images/gallery/monastery.webp",
    credit: "Wikimedia / Alexey Komarov, 2018",
  },
  {
    title: "Центр посёлка",
    caption: "Пушкинские Горы",
    url: "/images/gallery/village.jpg",
    webp: "/images/gallery/village.webp",
    credit: "Wikimedia / Alexey Komarov, 2018",
  },
  {
    title: "Памятник Пушкину",
    caption: "У Святогорского монастыря",
    url: "/images/gallery/monument.jpg",
    webp: "/images/gallery/monument.webp",
    credit: "Wikimedia Commons",
  },
  {
    title: "Тригорское",
    caption: "Дом Осиповых-Вульф, усадьба в заповеднике",
    url: "/images/gallery/trigorskoe.jpg",
    webp: "/images/gallery/trigorskoe.webp",
    credit: "Wikimedia Commons",
  },
  {
    title: "Петровское",
    caption: "Усадьба Ганнибалов у озера",
    url: "/images/gallery/petrovskoe.jpg",
    webp: "/images/gallery/petrovskoe.webp",
    credit: "Wikimedia Commons",
  },
];

export function quoteForPage(path: string): string {
  if (path === "/" || path === "") return PUSHKIN_QUOTES.home;
  if (path.startsWith("/ai")) return PUSHKIN_QUOTES.ai;
  if (path.startsWith("/map")) return PUSHKIN_QUOTES.map;
  if (path.startsWith("/services")) return PUSHKIN_QUOTES.services;
  if (path.startsWith("/classifieds")) return PUSHKIN_QUOTES.classifieds;
  if (path.startsWith("/register")) return PUSHKIN_QUOTES.register;
  return PUSHKIN_QUOTES.default;
}

export function yandexRouteUrl(lat: number, lng: number): string {
  return `https://yandex.ru/maps/?rtext=~${lat},${lng}&rtt=auto`;
}

export function yandexMapsPointUrl(lat: number, lng: number, name: string): string {
  return `https://yandex.ru/maps/?pt=${lng},${lat}&z=17&text=${encodeURIComponent(name + " Пушкинские Горы")}`;
}

/** Работает офлайн на телефоне — открывает навигатор по GPS */
export function geoNavigateUrl(lat: number, lng: number): string {
  return `geo:${lat},${lng}?q=${lat},${lng}`;
}
