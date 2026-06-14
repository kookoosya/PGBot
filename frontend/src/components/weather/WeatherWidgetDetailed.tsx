import { useMemo } from "react";
import { formatTemperature, formatUpdatedAt, useWeather } from "@/hooks/useWeather";
import type { WeatherHourlyItem } from "@/lib/api";

type DayForecast = {
  key: string;
  label: string;
  icon: string;
  min: number;
  max: number;
};

function buildDailyForecast(hourly: WeatherHourlyItem[]): DayForecast[] {
  const buckets = new Map<string, WeatherHourlyItem[]>();
  for (const hour of hourly) {
    const key = hour.time.slice(0, 10);
    const list = buckets.get(key) ?? [];
    list.push(hour);
    buckets.set(key, list);
  }

  return [...buckets.entries()].slice(0, 5).map(([key, hours]) => {
    const temps = hours.map((h) => h.temperature);
    const date = new Date(`${key}T12:00:00`);
    const label = date.toLocaleDateString("ru-RU", { weekday: "short", day: "numeric", month: "short" });
    const midday = hours[Math.min(4, hours.length - 1)];
    return {
      key,
      label,
      icon: midday.icon,
      min: Math.min(...temps),
      max: Math.max(...temps),
    };
  });
}

export function WeatherWidgetDetailed() {
  const { data, loading, error } = useWeather();

  const daily = useMemo(
    () => (data?.hourly ? buildDailyForecast(data.hourly) : []),
    [data?.hourly],
  );

  if (loading && !data) {
    return (
      <section className="weather-panel weather-panel--loading" aria-busy="true">
        <div className="weather-panel-head">
          <h2>🌤 Погода в посёлке</h2>
        </div>
        <p className="weather-panel-muted">Загружаем прогноз…</p>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="weather-panel">
        <div className="weather-panel-head">
          <h2>🌤 Погода в посёлке</h2>
        </div>
        <p className="weather-panel-muted">Прогноз временно недоступен.</p>
      </section>
    );
  }

  const { current, hourly } = data;

  return (
    <section className="weather-panel" aria-label={`Погода в ${data.location_name}`}>
      <div className="weather-panel-head">
        <div>
          <p className="weather-panel-kicker">{data.location_name}</p>
          <h2>🌤 Погода и прогноз</h2>
        </div>
        <p className="weather-panel-updated">Обновлено {formatUpdatedAt(data.updated_at)}</p>
      </div>

      <div className="weather-current-grid">
        <div className="weather-current-main">
          <span className="weather-current-icon" aria-hidden>
            {current.icon}
          </span>
          <div>
            <p className="weather-current-temp">{formatTemperature(current.temperature)}</p>
            <p className="weather-current-desc">{current.description}</p>
          </div>
        </div>

        <dl className="weather-metrics">
          <div>
            <dt>Ощущается</dt>
            <dd>{formatTemperature(current.apparent_temperature)}</dd>
          </div>
          <div>
            <dt>Влажность</dt>
            <dd>{current.humidity}%</dd>
          </div>
          <div>
            <dt>Ветер</dt>
            <dd>{current.wind_speed.toFixed(1)} м/с</dd>
          </div>
          <div>
            <dt>Осадки</dt>
            <dd>{current.precipitation > 0 ? `${current.precipitation.toFixed(1)} мм` : "нет"}</dd>
          </div>
        </dl>
      </div>

      {daily.length > 0 && (
        <div className="weather-daily">
          <h3 className="weather-hourly-title">По дням</h3>
          <div className="weather-daily-scroll" role="list">
            {daily.map((day) => (
              <article key={day.key} className="weather-day-card" role="listitem">
                <p className="weather-day-label">{day.label}</p>
                <span className="weather-day-icon" aria-hidden>{day.icon}</span>
                <p className="weather-day-temps">
                  {formatTemperature(day.max)} <span>{formatTemperature(day.min)}</span>
                </p>
              </article>
            ))}
          </div>
        </div>
      )}

      {hourly.length > 0 && (
        <div className="weather-hourly">
          <h3 className="weather-hourly-title">По часам</h3>
          <div className="weather-hourly-scroll" role="list">
            {hourly.map((hour) => (
              <article key={hour.time} className="weather-hour-card" role="listitem">
                <p className="weather-hour-time">{hour.hour_label}</p>
                <span className="weather-hour-icon" aria-hidden>
                  {hour.icon}
                </span>
                <p className="weather-hour-temp">{formatTemperature(hour.temperature)}</p>
                <p className="weather-hour-feels">
                  ощ. {formatTemperature(hour.apparent_temperature)}
                </p>
                {(hour.precipitation > 0 || hour.precipitation_probability) && (
                  <p className="weather-hour-precip">
                    {hour.precipitation > 0
                      ? `${hour.precipitation.toFixed(1)} мм`
                      : `${hour.precipitation_probability}%`}
                  </p>
                )}
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
