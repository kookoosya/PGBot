export interface SeasonalTip {
  icon: string;
  title: string;
  text: string;
  link?: string;
  linkLabel?: string;
}

/** Auto-generated seasonal hints — no manual content required. */
export function getSeasonalTip(): SeasonalTip | null {
  const month = new Date().getMonth() + 1;

  if (month >= 6 && month <= 8) {
    return {
      icon: "🌿",
      title: "Летний сезон",
      text: "Экскурсии в музее-заповеднике, маршруты для туристов и ярмарки — смотрите афишу и карту.",
      link: "/events",
      linkLabel: "Афиша событий",
    };
  }
  if (month === 12 || month === 1) {
    return {
      icon: "❄️",
      title: "Зимние праздники",
      text: "Концерты, ёлки в музее и мероприятия в Пскове — загляните в ближайшие события.",
      link: "/events",
      linkLabel: "Что происходит",
    };
  }
  if (month >= 4 && month <= 5) {
    return {
      icon: "🪻",
      title: "Весна в Пушкинских Горах",
      text: "Пушкинские праздники и первые экскурсии — следите за афишей музея.",
      link: "/events",
      linkLabel: "События",
    };
  }
  if (month >= 9 && month <= 10) {
    return {
      icon: "🍂",
      title: "Золотая осень",
      text: "Меньше туристов — удобное время для прогулок по усадьбам и поездки в Псков.",
      link: "/map",
      linkLabel: "Открыть карту",
    };
  }
  return null;
}
