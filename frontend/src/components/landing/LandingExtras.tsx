import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const RU_HOST = "pushkinskie-gory.ru";
const STORAGE_KEY = "pgbot-ru-banner-dismiss";

/** Подсказка жителям РФ: основной адрес .ru (пока .xyz блокируют). */
export function RuAccessBanner() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const host = window.location.hostname;
    if (host === RU_HOST || host === `www.${RU_HOST}`) return;
    if (sessionStorage.getItem(STORAGE_KEY)) return;
    setShow(true);
  }, []);

  if (!show) return null;

  return (
    <div className="ru-access-banner" role="status">
      <p className="ru-access-banner-text">
        Для России без VPN:{" "}
        <a href={`https://${RU_HOST}`} className="ru-access-banner-link">
          pushkinskie-gory.ru
        </a>
      </p>
      <button
        type="button"
        className="ru-access-banner-close"
        aria-label="Закрыть"
        onClick={() => {
          sessionStorage.setItem(STORAGE_KEY, "1");
          setShow(false);
        }}
      >
        ✕
      </button>
    </div>
  );
}

/** Нижняя строка главной — атмосфера «альбома». */
export function LandingClosingStrip() {
  return (
    <footer className="landing-closing" aria-label="О посёлке">
      <p className="landing-closing-verse">
        Михайловское · Святогорье · живое Пушкиногорье
      </p>
      <Link to="/map" className="landing-closing-link">
        Открыть карту посёлка →
      </Link>
    </footer>
  );
}
