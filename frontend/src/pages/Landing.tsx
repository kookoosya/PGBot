import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { QuickNav } from "@/components/QuickNav";
import { VillageGallery } from "@/components/VillageGallery";
import { BRAND } from "@/lib/branding";
import { api } from "@/lib/api";

const features = [
  { icon: "📋", title: "Объявления", desc: "Дрова, строительство, вакансии от жителей", to: "/classifieds" },
  { icon: "💇", title: "Услуги мастеров", desc: "Маникюр, стрижки — запись по расписанию", to: "/services" },
  { icon: "🗺", title: "Карта посёлка", desc: "Магазины, аптеки, отзывы и жалобы", to: "/map" },
  { icon: "🤖", title: "ИИ-помощник", desc: "Ответы о посёлке и помощь с текстом", to: "/ai" },
  { icon: "📅", title: "Кабинет мастера", desc: "Расписание, занятость, записи", to: "/services/cabinet" },
  { icon: "🏛", title: "Для служб", desc: "Регистрация и верификация сотрудников", to: "/register" },
];

const VK_BOT_URL = "https://vk.com";

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
          <p className="hero-quote">«Любви, надежды, тихой славы...»</p>
          <h2 className="hero-title">{BRAND.name}</h2>
          <p className="hero-tagline">{BRAND.tagline}</p>
          <p className="hero-desc">
            Объявления, мастера, карта магазинов и служб — всё для жителей в одном месте.
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
              <Link to="/ai" className="stat-pill">ИИ бесплатно</Link>
            </div>
          )}

          <div className="hero-actions">
            <Link to="/map" className="btn-hero-primary">🗺 Карта посёлка</Link>
            <Link to="/classifieds" className="btn-hero-secondary">📋 Объявления</Link>
            <Link to="/services" className="btn-hero-secondary">💇 Услуги</Link>
            <Link to="/ai" className="btn-hero-secondary">🤖 ИИ</Link>
          </div>
        </div>
      </section>

      <section className="page-section">
        <h3 className="section-title animate-in">Куда перейти</h3>
        <QuickNav />
      </section>

      <section className="section-alt">
        <div className="page-section">
          <h3 className="section-title animate-in">Всё на сайте</h3>
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

      <section className="page-section">
        <a
          href={VK_BOT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="vk-cta-card"
        >
          <span className="vk-cta-icon">📱</span>
          <div>
            <h3 className="vk-cta-title">Обращения жителей — бот ВКонтакте</h3>
            <p className="vk-cta-desc">
              Сообщите о проблеме в посёлке — дороги, мусор, освещение. Передадим ответственным службам.
            </p>
          </div>
          <span className="vk-cta-arrow">→</span>
        </a>
      </section>

      <section className="page-section">
        <div className="pushkin-card p-8 md:p-10 text-center max-w-2xl mx-auto animate-in">
          <span className="text-5xl">🪶</span>
          <blockquote className="mt-6 text-xl font-serif italic text-foreground/80 leading-relaxed">
            «Я памятник себе воздвиг нерукотворный,<br />
            К ногам его железный век не наступит...»
          </blockquote>
          <p className="mt-4 text-sm text-muted-foreground">
            А мы вместе возводим порядок и уют в нашем посёлке
          </p>
        </div>
      </section>

      <VillageGallery />
    </div>
  );
}
