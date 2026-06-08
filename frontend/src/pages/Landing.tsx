import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { VillageGallery } from "@/components/VillageGallery";
import { BRAND } from "@/lib/branding";
import { MAIN_SECTIONS } from "@/lib/navigation";
import { api } from "@/lib/api";
import { PUSHKIN_QUOTES } from "@/lib/pushkin";

const extraFeatures = [
  { icon: "📅", title: "Мастерам", desc: "Расписание, записи клиентов, кабинет", to: "/services/cabinet" },
  { icon: "✍️", title: "Регистрация", desc: "Жители, организации, ЖКХ, мастера", to: "/register" },
];

export function Landing() {
  const [stats, setStats] = useState({ places: 0, ads: 0 });

  useEffect(() => {
    api.getMapStats().then((s) => setStats((st) => ({ ...st, places: s.total_places }))).catch(() => {});
    api.getClassifieds().then((r) => setStats((st) => ({ ...st, ads: r.total }))).catch(() => {});
  }, []);

  const features = [
    ...MAIN_SECTIONS.filter((s) => s.to !== "/").map((s) => ({
      icon: s.icon,
      title: s.label,
      desc: sectionDesc[s.to] || "",
      to: s.to,
    })),
    ...extraFeatures,
  ];

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
          <p className="hero-desc">{BRAND.description}</p>
          <p className="hero-free-note">✨ Объявления, услуги и жалобы — бесплатно · ИИ — {30} сообщений/день</p>

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
            <Link to="/complaints" className="btn-hero-secondary">⚠️ Жалобы</Link>
            <Link to="/register" className="btn-hero-secondary">✍️ Регистрация</Link>
          </div>
        </div>
      </section>

      <section className="section-alt">
        <div className="page-section">
          <h3 className="section-title animate-in">Разделы портала</h3>
          <p className="text-center text-muted-foreground mb-8 max-w-xl mx-auto">
            Всё в одном месте — как на сайте, так и в VK-боте
          </p>
          <div className="feature-grid">
            {features.map((f, i) => (
              <Link
                key={f.to}
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

const sectionDesc: Record<string, string> = {
  "/map": "Магазины, аптеки, такси, гостиницы",
  "/classifieds": "Дрова, вакансии, услуги — от соседей",
  "/services": "Огород, дрова, покос, мастера с записью",
  "/complaints": "Сообщить о проблеме — ЖКХ, дороги, освещение",
  "/ai": "Вопросы о посёлке, тексты, идеи, картинки",
};
