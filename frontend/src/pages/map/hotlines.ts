/** Проверенные номера для посёлка — экстренные и полезные службы. */

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
  { icon: "🏛", name: "Администрация района", phone: "+7 (81146) 2-01-01", note: "Пн–Пт 09:00–18:00" },
  { icon: "🏥", name: "Поликлиника", phone: "+7 (81146) 2-13-61", note: "Приёмный покой 24/7" },
  { icon: "👶", name: "Детская поликлиника", phone: "+7 (81146) 2-18-97" },
  { icon: "🏛", name: "МФЦ", phone: "+7 (81146) 2-02-02", note: "Пн–Пт 09:00–18:00" },
  { icon: "📮", name: "Почта России", phone: "+7 (81146) 2-07-01", note: "Пн–Сб 08:00–18:00" },
  { icon: "🚌", name: "Автовокзал", phone: "+7 (81146) 2-05-05", note: "06:00–22:00" },
  { icon: "🏛", name: "Музей-заповедник", phone: "+7 (81146) 2-23-21", note: "Касса: +7 (81146) 2-26-09" },
  { icon: "💊", name: "Аптека-А (ул. Ленина)", phone: "+7 (81146) 2-12-87", note: "09:00–20:00" },
  { icon: "💊", name: "Аптека-А (Новоржевская)", phone: "+7 (81146) 6-07-11", note: "09:00–20:00" },
];
