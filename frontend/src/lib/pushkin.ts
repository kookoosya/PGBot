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

/** Фото Пушкиногорья — Wikimedia Commons, не стоковые карточки */
export const VILLAGE_PHOTOS = [
  {
    title: "Михайловское",
    caption: "Усадьба музея-заповедника А.С. Пушкина",
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/PushkinGory_asv2018-07_img13_Mikhailovskoe.jpg/960px-PushkinGory_asv2018-07_img13_Mikhailovskoe.jpg",
    credit: "Wikimedia / Alexey Komarov",
  },
  {
    title: "Святогорский монастырь",
    caption: "Пушкиногорская лавра над рекой Сороть",
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Svyatogorsky_Monastery_05.jpg/960px-Svyatogorsky_Monastery_05.jpg",
    credit: "Wikimedia Commons",
  },
  {
    title: "Центр посёлка",
    caption: "Пушкинские Горы — вид с высоты",
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/PushkinGory_asv2018-07_img01.jpg/960px-PushkinGory_asv2018-07_img01.jpg",
    credit: "Wikimedia / Alexey Komarov",
  },
  {
    title: "Памятник Пушкину",
    caption: "У Святогорского монастыря",
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Pushkin_monument_in_Pushkinskiye_Gory.jpg/960px-Pushkin_monument_in_Pushkinskiye_Gory.jpg",
    credit: "Wikimedia Commons",
  },
  {
    title: "Тригорское",
    caption: "Усадьба в заповеднике",
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Trigorskoe.jpg/960px-Trigorskoe.jpg",
    credit: "Wikimedia Commons",
  },
  {
    title: "Петровское",
    caption: "Усадьба Ганнибалов у озера",
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Petrovskoe_Pushkin_hills.jpg/960px-Petrovskoe_Pushkin_hills.jpg",
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
