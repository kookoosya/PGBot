/** Экстренные номера — официальные службы РФ. Остальные контакты — из public places API. */

export type HotlineEntry = {
  icon: string;
  name: string;
  phone: string;
  note?: string;
  emergency?: boolean;
};

export const EMERGENCY_HOTLINES: HotlineEntry[] = [
  { icon: "🆘", name: "Единый номер экстренных служб", phone: "112", note: "Бесплатно с мобильного и стационарного телефона", emergency: true },
  { icon: "🚑", name: "Скорая помощь", phone: "103", emergency: true },
  { icon: "🚒", name: "Пожарная охрана", phone: "101", emergency: true },
  { icon: "👮", name: "Полиция", phone: "102", emergency: true },
  { icon: "⛽", name: "Аварийная газовая служба", phone: "104", emergency: true },
];

/** @deprecated Используйте EMERGENCY_HOTLINES + verifiedPhoneContacts из API */
export const VILLAGE_HOTLINES = EMERGENCY_HOTLINES;
