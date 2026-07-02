/** Экстренные номера и контакты с официальных сайтов (этап 1). */

export type HotlineEntry = {
  icon: string;
  name: string;
  phone: string;
  note?: string;
  emergency?: boolean;
};

export const VILLAGE_HOTLINES: HotlineEntry[] = [
  { icon: "🆘", name: "Единый номер экстренных служб", phone: "112", note: "112 или 911 с мобильного", emergency: true },
  { icon: "🚑", name: "Скорая помощь", phone: "103", emergency: true },
  { icon: "🚒", name: "Пожарная охрана", phone: "101", emergency: true },
  { icon: "👮", name: "Полиция", phone: "102", emergency: true },
  { icon: "⛽", name: "Аварийная газовая служба", phone: "104", emergency: true },
  {
    icon: "🏛",
    name: "Государственный музей-заповедник А. С. Пушкина «Михайловское»",
    phone: "+7 (81146) 2-23-21",
    note: "Касса и экскурсии: +7 (81146) 2-26-09 · pushkinland.ru",
  },
  {
    icon: "⛪",
    name: "Свято-Успенский Святогорский мужской монастырь",
    phone: "+7 (81146) 2-33-89",
    note: "svyatogorskiy-monastery.ru",
  },
  {
    icon: "🏥",
    name: 'Филиал «Пушкиногорский» ГБУЗ ПО «Островская МБ»',
    phone: "+7 (81146) 2-27-06",
    note: "Детская консультация: +7 (81146) 2-18-97 · ostrovmb.ru",
  },
];
