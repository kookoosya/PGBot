import { formatTemperature, useWeather } from "@/hooks/useWeather";

type Props = {
  variant?: "header" | "inline";
};

export function WeatherWidgetCompact({ variant = "inline" }: Props) {
  const { data, loading, error } = useWeather();

  if (loading && !data) {
    return (
      <div className={`weather-compact weather-compact--${variant}`} aria-busy="true">
        <span className="weather-compact-icon">🌤</span>
        <span className="weather-compact-text">Загрузка…</span>
      </div>
    );
  }

  if (error || !data) {
    return null;
  }

  const { current } = data;

  return (
    <div
      className={`weather-compact weather-compact--${variant}`}
      title={`${current.description}. Ощущается ${formatTemperature(current.apparent_temperature)}`}
      aria-label={`Погода в ${data.location_name}: ${formatTemperature(current.temperature)}, ${current.description}`}
    >
      <span className="weather-compact-icon" aria-hidden>
        {current.icon}
      </span>
      <span className="weather-compact-temp">{formatTemperature(current.temperature)}</span>
      <span className="weather-compact-desc">{current.description}</span>
    </div>
  );
}
