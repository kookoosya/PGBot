import type { WeatherResponse } from "@/lib/api";

const LAT = 57.0267;
const LNG = 28.91;
const TZ = "Europe/Moscow";

const WEATHER_META: Record<number, [string, string]> = {
  0: ["Ясно", "☀️"],
  1: ["Преимущественно ясно", "🌤"],
  2: ["Переменная облачность", "⛅"],
  3: ["Пасмурно", "☁️"],
  45: ["Туман", "🌫"],
  48: ["Изморозь", "🌫"],
  51: ["Морось", "🌦"],
  53: ["Морось", "🌦"],
  55: ["Морось", "🌦"],
  61: ["Дождь", "🌧"],
  63: ["Дождь", "🌧"],
  65: ["Ливень", "🌧"],
  71: ["Снег", "🌨"],
  73: ["Снег", "🌨"],
  75: ["Снегопад", "❄️"],
  80: ["Ливень", "🌦"],
  81: ["Ливень", "🌦"],
  82: ["Сильный ливень", "⛈"],
  95: ["Гроза", "⛈"],
};

function meta(code: number) {
  const [description, icon] = WEATHER_META[code] ?? ["Неизвестно", "🌡"];
  return { description, icon };
}

/** Прямой запрос к Open-Meteo, если backend ещё без /weather (старый прод). */
export async function fetchWeatherDirect(): Promise<WeatherResponse | null> {
  const params = new URLSearchParams({
    latitude: String(LAT),
    longitude: String(LNG),
    timezone: TZ,
    forecast_days: "2",
    current: "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
    hourly: "temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
  });

  const response = await fetch(`https://api.open-meteo.com/v1/forecast?${params}`);
  if (!response.ok) return null;

  const payload = await response.json();
  const currentRaw = payload.current;
  const hourlyRaw = payload.hourly;
  if (!currentRaw || !hourlyRaw?.time) return null;

  const code = Number(currentRaw.weather_code ?? 0);
  const { description, icon } = meta(code);
  const now = new Date();

  const hourly = (hourlyRaw.time as string[])
    .map((time: string, idx: number) => {
      const hourDate = new Date(time);
      if (hourDate < now) return null;
      const hourCode = Number(hourlyRaw.weather_code?.[idx] ?? 0);
      const hourMeta = meta(hourCode);
      return {
        time,
        hour_label: hourDate.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }),
        temperature: Number(hourlyRaw.temperature_2m?.[idx] ?? 0),
        apparent_temperature: Number(hourlyRaw.apparent_temperature_2m?.[idx] ?? 0),
        precipitation: Number(hourlyRaw.precipitation?.[idx] ?? 0),
        precipitation_probability: null,
        humidity: null,
        wind_speed: Number(hourlyRaw.wind_speed_10m?.[idx] ?? 0),
        weather_code: hourCode,
        description: hourMeta.description,
        icon: hourMeta.icon,
      };
    })
    .filter(Boolean)
    .slice(0, 24) as WeatherResponse["hourly"];

  return {
    location_name: "Пушкинские Горы",
    latitude: LAT,
    longitude: LNG,
    timezone: TZ,
    updated_at: now.toISOString(),
    current: {
      temperature: Number(currentRaw.temperature_2m ?? 0),
      apparent_temperature: Number(currentRaw.apparent_temperature_2m ?? 0),
      humidity: Number(currentRaw.relative_humidity_2m ?? 0),
      precipitation: Number(currentRaw.precipitation ?? 0),
      wind_speed: Number(currentRaw.wind_speed_10m ?? 0),
      weather_code: code,
      description,
      icon,
      time: now.toISOString(),
    },
    hourly,
    cache_ttl_seconds: 1800,
  };
}
