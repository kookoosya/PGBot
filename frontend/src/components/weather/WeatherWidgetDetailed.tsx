import { formatTemperature, formatUpdatedAt, useWeather } from "@/hooks/useWeather";

export function WeatherWidgetDetailed() {
  const { data, loading, error } = useWeather();

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
          <h2>🌤 Погода сейчас</h2>
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

      {hourly.length > 0 && (
        <div className="weather-hourly">
          <h3 className="weather-hourly-title">Почасовой прогноз</h3>
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
