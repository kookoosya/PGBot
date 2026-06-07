import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { QuickNav } from "@/components/QuickNav";
import { VillageGallery } from "@/components/VillageGallery";
import { BRAND } from "@/lib/branding";
import { api } from "@/lib/api";
import { PUSHKIN_QUOTES, VILLAGE_PHOTOS } from "@/lib/pushkin";

const features = [
  { icon: "📋", title: "Объявления", desc: "150 ₽ за объявление — дрова, вакансии, услуги", to: "/classifieds" },
  { icon: "💇", title: "Услуги мастеров", desc: "Маникюр, стрижки — запись по расписанию", to: "/services" },
  { icon: "🗺", title: "Карта посёлка", desc: "Магазины, аптеки, отзывы и жалобы", to: "/map" },
  { icon: "🤖", title: "ИИ-помощник", desc: "Ответы о посёлке и помощь с текстом", to: "/ai" },
  { icon: "📅", title: "Кабинет мастера", desc: "Расписание, занятость, записи", to: "/services/cabinet" },
  { icon: "🏛", title: "Для служб", desc: "Регистрация и верификация сотрудников", to: "/register" },
];

const POET_FACTS = [
  { year: "1799", text: "Александр Пушкин родился в Москве" },
  { year: "1817", text: "Первое посещение Михайловского — ссылка отца" },
  { year: "1824", text: "Ссылка в Михайловское — великие творения" },
  { year: "1837", text: "Пушкинские Горы — место последнего приюта поэта" },
];

export function Landing() {
  const [stats, setStats] = useState({ places: 0, ads: 0 });
  const vkUrl = "https://vk.com";

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
            Земля поэта — наш дом. Объявления, мастера, карта и ИИ-помощник для жителей посёлка.
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

      <section className="pushkin-timeline section-alt">
        <div className="page-section">
          <h3 className="section-title">Пушкин и эти места</h3>
          <div className="timeline-row">
            {POET_FACTS.map((f) => (
              <div key={f.year} className="timeline-item">
                <span className="timeline-year">{f.year}</span>
                <p className="timeline-text">{f.text}</p>
              </div>
            ))}
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
        <div className="pushkin-heritage-grid">
          {VILLAGE_PHOTOS.map((photo) => (
            <div key={photo.title} className="pushkin-heritage-card">
              <img src={photo.url} alt={photo.title} loading="lazy" />
              <div className="pushkin-heritage-caption">
                <h4>{photo.title}</h4>
                <p>{photo.caption}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="page-section">
        <a
          href={vkUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="vk-cta-card"
        >
          <span className="vk-cta-icon">📱</span>
          <div>
            <h3 className="vk-cta-title">Бот ВКонтакте — обращения и уведомления</h3>
            <p className="vk-cta-desc">
              Сообщите о проблеме в посёлке. Уведомления о записях и объявлениях — сразу в ВК.
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
