import { Link } from "react-router-dom";
import { formatTemperature } from "@/hooks/useWeather";
import { formatTodayUpdatedAt, useToday } from "@/hooks/useToday";
import { formatDate } from "@/lib/utils";

export function TodayInVillage() {
  const { data, loading, error } = useToday();

  if (loading && !data) {
    return (
      <section className="today-panel" aria-busy="true">
        <div className="today-panel-head">
          <h2>Сегодня в посёлке</h2>
        </div>
        <p className="today-muted">Собираем актуальную информацию…</p>
      </section>
    );
  }

  if (error && !data) {
    return (
      <section className="today-panel">
        <div className="today-panel-head">
          <h2>Сегодня в посёлке</h2>
        </div>
        <p className="today-muted">Сводка временно недоступна.</p>
      </section>
    );
  }

  if (!data) return null;

  const weather = data.weather?.current;
  const ad = data.latest_classified;

  return (
    <section className="today-panel" aria-label="Сегодня в посёлке">
      <div className="today-panel-head">
        <div>
          <p className="today-kicker">🪶 Актуально сейчас</p>
          <h2>Сегодня в посёлке</h2>
        </div>
        <p className="today-updated">Обновлено {formatTodayUpdatedAt(data.updated_at)}</p>
      </div>

      <div className="today-grid">
        <article className="today-card today-card-weather">
          <h3 className="today-card-title">Погода</h3>
          {weather ? (
            <>
              <div className="today-weather-main">
                <span className="today-weather-icon" aria-hidden>{weather.icon}</span>
                <div>
                  <p className="today-weather-temp">{formatTemperature(weather.temperature)}</p>
                  <p className="today-weather-desc">{weather.description}</p>
                </div>
              </div>
              <ul className="today-weather-meta">
                <li>Ощущается {formatTemperature(weather.apparent_temperature)}</li>
                <li>Влажность {weather.humidity}%</li>
                <li>Ветер {weather.wind_speed.toFixed(1)} м/с</li>
              </ul>
              {data.weather && data.weather.hourly.length > 0 && (
                <div className="today-hourly-mini">
                  {data.weather.hourly.slice(0, 6).map((hour) => (
                    <span key={hour.time} className="today-hour-chip">
                      {hour.hour_label} {hour.icon} {formatTemperature(hour.temperature)}
                    </span>
                  ))}
                </div>
              )}
            </>
          ) : (
            <p className="today-muted">Прогноз временно недоступен</p>
          )}
        </article>

        <article className="today-card today-card-ad">
          <h3 className="today-card-title">Свежее объявление</h3>
          {ad ? (
            <>
              <p className="today-ad-category">{ad.category_label}</p>
              <Link to={`/classifieds/${ad.id}`} className="today-ad-link">
                {ad.title}
              </Link>
              <p className="today-ad-date">{formatDate(ad.created_at)}</p>
            </>
          ) : (
            <p className="today-muted">Пока нет новых объявлений</p>
          )}
          <Link to="/classifieds" className="today-card-action">
            Все объявления →
          </Link>
        </article>

        <article className="today-card today-card-map">
          <h3 className="today-card-title">Карта посёлка</h3>
          <dl className="today-map-stats">
            <div>
              <dt>Организаций</dt>
              <dd>{data.map.total_places}</dd>
            </div>
            <div>
              <dt>Отзывов</dt>
              <dd>{data.map.total_reviews}</dd>
            </div>
            <div>
              <dt>Такси</dt>
              <dd>{data.map.active_taxi_count}</dd>
            </div>
            <div>
              <dt>Маршрутов</dt>
              <dd>{data.map.route_count}</dd>
            </div>
          </dl>
          <Link to="/map" className="today-card-action">
            Открыть карту →
          </Link>
        </article>
      </div>
    </section>
  );
}
