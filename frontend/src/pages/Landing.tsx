import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { VillageGallery } from "@/components/VillageGallery";
import { BRAND } from "@/lib/branding";
import { api } from "@/lib/api";
import { PUSHKIN_QUOTES } from "@/lib/pushkin";

const features = [
  { icon: "📋", title: "Объявления", desc: "Дрова, вакансии, услуги — от соседей", to: "/classifieds" },
  { icon: "💇", title: "Услуги мастеров", desc: "Маникюр, стрижки — запись онлайн", to: "/services" },
  { icon: "🗺", title: "Карта", desc: "Магазины, аптеки, такси, гостиницы", to: "/map" },
  { icon: "🤖", title: "ИИ-помощник", desc: "Вопросы о посёлке и быте", to: "/ai" },
  { icon: "👤", title: "Регистрация", desc: "Жители, организации, службы", to: "/register" },
];

export function Landing() {
  const [stats, setStats] = useState({ places: 0, ads: 0 });

  useEffect(() => {
    api.getMapStats().then((s) => setStats((st) => ({ ...st, places: s.total_places }))).catch(() => {});
    api.getClassifieds().then((r) => setStats((st) => ({ ...st, ads: r.total }))).catch(() => {});
  }, []);

  return (
    <div className="landing-page">
      <section className="pushkin-gradient hero-section">
        <div className="hero-glow" aria-hidden />
        <div className="absolute inset-0 opacity-10 feather-pattern" />
        <div className="hero-content animate-hero">
          <p className="hero-badge">🪶 {BRAND.district}</p>
          <p className="hero-quote">{PUSHKIN_QUOTES.home}</p>
          <h2 className="hero-title">{BRAND.name}</h2>
          <p className="hero-tagline">{BRAND.tagline}</p>
          <p className="hero-desc">
            Карта, объявления, услуги мастеров — для жителей и гостей Пушкиногорья.
          </p>

          {(stats.places > 0 || stats.ads > 0) && (
            <div className="stats-bar">
              {stats.places > 0 && (
                <Link to="/map" className="stat-pill">
                  <strong>{stats.places}</strong> на карте
                </Link>
              )}
              <Link to="/classifieds" className="stat-pill">
                <strong>{stats.ads}</strong> объявлений
              </Link>
            </div>
          )}

          <div className="hero-actions">
            <Link to="/map" className="btn-hero-primary">🗺 Карта</Link>
            <Link to="/classifieds" className="btn-hero-secondary">📋 Объявления</Link>
            <Link to="/register" className="btn-hero-secondary">✍️ Регистрация</Link>
          </div>
        </div>
      </section>

      <section className="section-alt">
        <div className="page-section">
          <h3 className="section-title animate-in">Разделы портала</h3>
          <div className="feature-grid">
            {features.map((f, i) => (
              <Link
                key={f.title}
                to={f.to}
                className="feature-card no-underline text-inherit animate-in"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="feature-icon">{f.icon}</div>
                <h4 className="feature-title">{f.title}</h4>
                <p className="feature-desc">{f.desc}</p>
                <span className="feature-go">Открыть →</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <VillageGallery />
    </div>
  );
}
