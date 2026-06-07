export const PUSHKIN_QUOTES: Record<string, string> = {
  home: "«Любви, надежды, тихой славы\nНедолго сердцу снабжать...»",
  ai: "«Счастье то, что дух просветляет.»",
  map: "«Здесь русский дух... здесь Русью пахнет!»",
  services: "«Труд — вот лучшая зарядка для юности!»",
  classifieds: "«Всё, что ни делается, — к лучшему.»",
  register: "«Береги минуту — час сбережёшь.»",
  default: "«Я памятник себе воздвиг нерукотворный...»",
};

export const VILLAGE_PHOTOS = [
  {
    title: "Михайловское",
    caption: "Музей-заповедник А.С. Пушкина",
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Mikhailovskoe_park.jpg/800px-Mikhailovskoe_park.jpg",
  },
  {
    title: "Пушкиногорская лавра",
    caption: "Свято-Успенский монастырь",
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Pushkinskiye_Gory_Lavra.jpg/800px-Pushkinskiye_Gory_Lavra.jpg",
  },
  {
    title: "Пушкинские Горы",
    caption: "Посёлок поэтической земли",
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Pushkin_hills.jpg/800px-Pushkin_hills.jpg",
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
