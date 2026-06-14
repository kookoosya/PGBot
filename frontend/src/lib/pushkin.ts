export const PUSHKIN_QUOTES: Record<string, string> = {
  home: "«Любви, надежды, тихой славы\nНедолго сердцу снабжать...»",
  ai: "«Счастье то, что дух просветляет.»",
  map: "«Здесь русский дух... здесь Русью пахнет!»",
  jobs: "«Труд — вот лучшая зарядка для юности!»",
  services: "«Труд — вот лучшая зарядка для юности!»",
  classifieds: "«Всё, что ни делается, — к лучшему.»",
  complaints: "«Нет, я не льщу себя надеждой...»",
  wishes: "«Мечты, мечты,\nГде ваша сладость?»",
  register: "«Береги минуту — час сбережёшь.»",
  default: "«Я памятник себе воздвиг нерукотворный...»",
};

/** Герой главной — одна строка, крупно */
export const HERO_VERSE =
  "«Любви, надежды, тихой славы\nНедолго сердцу снабжать...»";

export type PushkinVerse = {
  text: string;
  source: string;
};

/** Блок стихов на главной — без навигации, только поэзия */
export const LANDING_VERSES: PushkinVerse[] = [
  {
    text: "«Здесь русский дух... здесь Русью пахнет!»",
    source: "«Медный всадник»",
  },
  {
    text: "«У лужайки, на опушке\nМахают, снявши шляпы...»",
    source: "«У лужайки»",
  },
  {
    text: "«Я памятник себе воздвиг нерукотворный,\nК нему не зарастёт народная тропа...»",
    source: "«Я памятник...»",
  },
  {
    text: "«Уж небо осенью дышало,\nУж более ручейков не бежало...»",
    source: "«Осень»",
  },
  {
    text: "«Всё, что ни делается, — к лучшему.»",
    source: "К Чаадаеву",
  },
  {
    text: "«Труд — вот лучшая зарядка для юности!»",
    source: "«Дубровский»",
  },
  {
    text: "«Счастье то, что дух просветляет.»",
    source: "К Чаадаеву",
  },
  {
    text: "«Мечты, мечты,\nГде ваша сладость?»",
    source: "«Во глубине сибирских руд»",
  },
];

/** Короткая строка к фото мест */
export const PHOTO_VERSES: Record<string, string> = {
  Михайловское: "«...и снова я у вас, мои друзья...»",
  "Святогорский монастырь": "«И памятник надгробный там\nСтоит, уныло над Соротью...»",
  "НКЦ «Пушкинские Горы»": "«Здесь русский дух... здесь Русью пахнет!»",
  "Памятник Пушкину": "«Я памятник себе воздвиг нерукотворный...»",
  Тригорское: "«У лужайки, на опушке\nМахают, снявши шляпы...»",
  Петровское: "«Уж небо осенью дышало...»",
};

export { SITE_URL } from "./siteUrl";

export type VillagePhoto = {
  title: string;
  caption: string;
  url: string;
  webp: string;
};

/** Фото Пушкиногорья */
export const VILLAGE_PHOTOS: VillagePhoto[] = [
  {
    title: "Михайловское",
    caption: "Усадьба музея-заповедника А.С. Пушкина",
    url: "/images/gallery/mikhailovskoe.jpg",
    webp: "/images/gallery/mikhailovskoe.webp",
  },
  {
    title: "Святогорский монастырь",
    caption: "Пушкиногорская лавра над рекой Сороть",
    url: "/images/gallery/monastery.jpg",
    webp: "/images/gallery/monastery.webp",
  },
  {
    title: "НКЦ «Пушкинские Горы»",
    caption:
      "Научно-культурный центр музея-заповедника — белое здание с колоннами на въезде в посёлок",
    url: "/images/gallery/nkc.jpg",
    webp: "/images/gallery/nkc.webp",
  },
  {
    title: "Памятник Пушкину",
    caption: "У Святогорского монастыря",
    url: "/images/gallery/monument.jpg",
    webp: "/images/gallery/monument.webp",
  },
  {
    title: "Тригорское",
    caption: "Дом Осиповых-Вульф, усадьба в заповеднике",
    url: "/images/gallery/trigorskoe.jpg",
    webp: "/images/gallery/trigorskoe.webp",
  },
  {
    title: "Петровское",
    caption: "Усадьба Ганнибалов у озера",
    url: "/images/gallery/petrovskoe.jpg",
    webp: "/images/gallery/petrovskoe.webp",
  },
];

export function quoteForPage(path: string): string {
  if (path === "/" || path === "") return PUSHKIN_QUOTES.home;
  if (path.startsWith("/ai")) return PUSHKIN_QUOTES.ai;
  if (path.startsWith("/map")) return PUSHKIN_QUOTES.map;
  if (path.startsWith("/jobs")) return PUSHKIN_QUOTES.jobs;
  if (path.startsWith("/services")) return PUSHKIN_QUOTES.services;
  if (path.startsWith("/classifieds")) return PUSHKIN_QUOTES.classifieds;
  if (path.startsWith("/complaints")) return PUSHKIN_QUOTES.complaints;
  if (path.startsWith("/wishes")) return PUSHKIN_QUOTES.wishes;
  if (path.startsWith("/register")) return PUSHKIN_QUOTES.register;
  return PUSHKIN_QUOTES.default;
}

export function yandexRouteUrl(lat: number, lng: number): string {
  return `https://yandex.ru/maps/?rtext=~${lat},${lng}&rtt=auto`;
}

export function yandexMapsPointUrl(lat: number, lng: number, name: string): string {
  return `https://yandex.ru/maps/?pt=${lng},${lat}&z=17&text=${encodeURIComponent(name + " Пушкинские Горы")}`;
}

export function geoNavigateUrl(lat: number, lng: number): string {
  return `geo:${lat},${lng}?q=${lat},${lng}`;
}
