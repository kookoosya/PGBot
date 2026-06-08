import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { VillageGallery } from "@/components/VillageGallery";
import { VkBotLink } from "@/components/VkBotLink";
import { BRAND } from "@/lib/branding";
import { MAIN_SECTIONS } from "@/lib/navigation";
import { api } from "@/lib/api";
import { PUSHKIN_QUOTES, VILLAGE_PHOTOS } from "@/lib/pushkin";
import { FALLBACK_HTTP_URL, PRIMARY_SITE_URL } from "@/lib/siteUrl";

const heroPhoto = VILLAGE_PHOTOS[0];

const highlights = [
  { n: "01", icon: "🗺", title: "Живая карта", desc: "Магазины, аптеки, такси, гостиницы — обновление каждые 6 часов", to: "/map", tone: "emerald" },
  { n: "02", icon: "📋", title: "Объявления", desc: "Дрова, вакансии, услуги от соседей — бесплатно", to: "/classifieds", tone: "gold" },
  { n: "03", icon: "⚠️", title: "Жалобы", desc: "Дороги, ЖКХ, освещение — официальный канал для жителей", to: "/complaints", tone: "rose" },
  { n: "04", icon: "🤖", title: "ИИ-помощник", desc: "30 сообщений в день — тексты, идеи, ответы о посёлке", to: "/ai", tone: "violet" },
];

export function Landing() {
  const [stats, setStats] = useState({ places: 0, ads: 0, loaded: false });

  useEffect(() => {
    Promise.all([
      api.getMapStats().then((s) => s.total_places).catch(() => 0),
      api.getClassifieds().then((r) => r.total).catch(() => 0),
    ]).then(([places, ads]) => setStats({ places, ads, loaded: true }));
  }, []);

  const quickSections = MAIN_SECTIONS.filter((s) => s.to !== "/");

  return (
    <div className="landing-epic">
      <section className="epic-hero">
        <div className="epic-hero-bg" aria-hidden>
          <picture>
            <source srcSet={heroPhoto.webp} type="image/webp" />
            <img src={heroPhoto.url} alt="" className="epic-hero-photo" />
          </picture>
          <div className="epic-hero-scrim" />
          <div className="epic-hero-mesh" />
        </div>

        <div className="epic-hero-inner">
          <div className="epic-hero-copy animate-hero">
            <span className="epic-kicker">🪶 {BRAND.district}</span>
            <p className="epic-quote">{PUSHKIN_QUOTES.home}</p>
            <h1 className="epic-title">
              <span className="epic-title-line">{BRAND.name}</span>
              <span className="epic-title-sub">{BRAND.tagline}</span>
            </h1>
            <p className="epic-lead">{BRAND.description}</p>

            <div className="epic-stats-row">
              <Link to="/map" className="epic-stat-card">
                <strong>{stats.loaded ? stats.places : "…"}</strong>
                <span>организаций на карте</span>
              </Link>
              <Link to="/classifieds" className="epic-stat-card">
                <strong>{stats.loaded ? stats.ads : "…"}</strong>
                <span>объявлений соседей</span>
              </Link>
              <div className="epic-stat-card epic-stat-card-static">
                <strong>6 ч</strong>
                <span>обновление справочника</span>
              </div>
            </div>

            <div className="epic-cta-row">
              <Link to="/map" className="epic-btn epic-btn-primary">🗺 Открыть карту</Link>
              <Link to="/classifieds" className="epic-btn epic-btn-glass">📋 Объявления</Link>
              <Link to="/complaints" className="epic-btn epic-btn-glass">⚠️ Подать жалобу</Link>
            </div>

            <div className="epic-access-note">
              <strong>Без VPN:</strong>{" "}
              <a href={PRIMARY_SITE_URL} className="epic-access-link">{PRIMARY_SITE_URL.replace("https://", "")}</a>
              {" · "}
              <a href={FALLBACK_HTTP_URL} className="epic-access-link">по IP</a>
            </div>
          </div>

          <div className="epic-hero-panel animate-in">
            <p className="epic-panel-label">Разделы портала</p>
            <div className="epic-panel-grid">
              {quickSections.map((s) => (
                <Link key={s.to} to={s.to} className="epic-panel-tile">
                  <span className="epic-panel-icon">{s.icon}</span>
                  <span className="epic-panel-text">{s.label}</span>
                </Link>
              ))}
              <Link to="/register" className="epic-panel-tile epic-panel-tile-accent">
                <span className="epic-panel-icon">✍️</span>
                <span className="epic-panel-text">Регистрация</span>
              </Link>
            </div>
            <div className="epic-panel-vk">
              <VkBotLink />
            </div>
          </div>
        </div>
      </section>

      <section className="epic-bento-section">
        <div className="page-section">
          <div className="epic-section-head">
            <p className="epic-section-kicker">Всё в одном месте</p>
            <h2 className="epic-section-title">Портал, который реально работает</h2>
            <p className="epic-section-desc">Карта, объявления, услуги, жалобы и ИИ — на сайте и в VK-боте</p>
          </div>

          <div className="epic-bento">
            {highlights.map((item, i) => (
              <Link
                key={item.to}
                to={item.to}
                className={`epic-bento-card epic-bento-${item.tone} animate-in`}
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <span className="epic-bento-num">{item.n}</span>
                <span className="epic-bento-icon">{item.icon}</span>
                <h3 className="epic-bento-title">{item.title}</h3>
                <p className="epic-bento-desc">{item.desc}</p>
                <span className="epic-bento-go">Перейти →</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="epic-strip">
        <div className="page-section epic-strip-inner">
          <div>
            <p className="epic-strip-kicker">Для туристов и жителей</p>
            <h2 className="epic-strip-title">Карта посёлка с рейтингами и маршрутами</h2>
            <p className="epic-strip-desc">Аптеки, магазины, кафе, такси, гостиницы — с отзывами и кнопкой «Построить маршрут»</p>
          </div>
          <Link to="/map" className="epic-btn epic-btn-primary epic-btn-lg">Смотреть на карте</Link>
        </div>
      </section>

      <VillageGallery />
    </div>
  );
}
