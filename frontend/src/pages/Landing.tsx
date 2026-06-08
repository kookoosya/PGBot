import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { VillageGallery } from "@/components/VillageGallery";
import { VkBotBanner, VkBotLink } from "@/components/VkBotLink";
import { BRAND } from "@/lib/branding";
import { MAIN_SECTIONS } from "@/lib/navigation";
import { api, ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { PUSHKIN_QUOTES, VILLAGE_PHOTOS } from "@/lib/pushkin";

const heroPhoto = VILLAGE_PHOTOS[0];

const highlights = [
  { n: "01", icon: "🗺", title: "Карта", desc: "Магазины, такси, музеи и 11 туристических маршрутов", to: "/map", tone: "sky" },
  { n: "02", icon: "📋", title: "Объявления", desc: "Дрова, услуги, продажа — бесплатно, без регистрации", to: "/classifieds", tone: "gold" },
  { n: "03", icon: "💼", title: "Работа", desc: "Вакансии и подработка от местных работодателей", to: "/classifieds?jobs=1", tone: "emerald" },
  { n: "04", icon: "⚠️", title: "Жалобы", desc: "Дороги, ЖКХ, освещение — официальный канал для жителей", to: "/complaints", tone: "rose" },
  { n: "05", icon: "🤖", title: "ИИ-помощник", desc: "30 сообщений в день — тексты, идеи, ответы о посёлке", to: "/ai", tone: "violet" },
];

export function Landing() {
  const [stats, setStats] = useState({ places: 0, ads: 0, jobs: 0, loaded: false });
  const [jobAds, setJobAds] = useState<ClassifiedAd[]>([]);

  useEffect(() => {
    Promise.all([
      api.getMapStats().then((s) => s.total_places).catch(() => 0),
      api.getClassifieds().then((r) => r.total).catch(() => 0),
      api.getClassifieds({ jobs_only: "true", page_size: "4" }).then((r) => r).catch(() => ({ items: [], total: 0 })),
    ]).then(([places, ads, jobsRes]) => {
      setStats({ places, ads, jobs: jobsRes.total, loaded: true });
      setJobAds(jobsRes.items);
    });
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
              <div className="epic-stat-card epic-stat-card-static">
                <strong>{stats.loaded ? stats.places : "…"}</strong>
                <span>мест на карте</span>
              </div>
              <div className="epic-stat-card epic-stat-card-static">
                <strong>{stats.loaded ? stats.ads : "…"}</strong>
                <span>объявлений соседей</span>
              </div>
              <div className="epic-stat-card epic-stat-card-static">
                <strong>{stats.loaded ? stats.jobs : "…"}</strong>
                <span>вакансий сейчас</span>
              </div>
            </div>

            <div className="epic-cta-row">
              <Link to="/map" className="epic-btn epic-btn-primary">🗺 Карта посёлка</Link>
              <Link to="/classifieds" className="epic-btn epic-btn-glass">📋 Объявление</Link>
              <Link to="/complaints" className="epic-btn epic-btn-glass">⚠️ Жалоба</Link>
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
            <h2 className="epic-section-title">Портал для жителей и гостей</h2>
            <p className="epic-section-desc">Объявления, работа, услуги, жалобы и ИИ — на сайте и в VK-боте</p>
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

      <section className="epic-jobs-section">
        <div className="page-section">
          <div className="epic-jobs-head">
            <div>
              <p className="epic-section-kicker">Работа в посёлке</p>
              <h2 className="epic-section-title epic-jobs-title">Вакансии и подработка</h2>
              <p className="epic-section-desc epic-jobs-desc">
                Местные работодатели — без посредников. Разместить вакансию можно бесплатно, регистрация не нужна.
              </p>
            </div>
            <Link to="/classifieds?jobs=1" className="epic-btn epic-btn-primary">Все вакансии</Link>
          </div>

          <div className="epic-jobs-grid">
            {jobAds.map((ad) => {
              const visual = getCategoryVisual(ad.category);
              return (
                <Link key={ad.id} to={`/classifieds/${ad.id}`} className="epic-job-card no-underline text-inherit">
                  <div className="epic-job-icon" style={{ background: visual.gradient }}>
                    {visual.icon}
                  </div>
                  <div className="epic-job-body">
                    <span className="epic-job-badge">{ad.category_label}</span>
                    <h3 className="epic-job-title">{ad.title}</h3>
                    <p className="epic-job-desc">{ad.description.slice(0, 120)}{ad.description.length > 120 ? "…" : ""}</p>
                    {ad.price != null && (
                      <p className="epic-job-pay">{ad.price} {ad.price_unit || "₽"}</p>
                    )}
                    <p className="epic-job-contact">
                      📞 <a href={`tel:${ad.phone.replace(/\s/g, "")}`} className="clickable-phone">{ad.phone}</a>
                    </p>
                  </div>
                </Link>
              );
            })}
            {jobAds.length === 0 && (
              <div className="epic-job-empty">
                <p>Пока нет опубликованных вакансий.</p>
                <Link to="/classifieds?jobs=1" className="epic-btn epic-btn-glass">Разместить первую</Link>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="epic-vk-section">
        <div className="page-section max-w-3xl">
          <div className="epic-section-head mb-6">
            <p className="epic-section-kicker">В VK тоже</p>
            <h2 className="epic-section-title">Бот в сообщениях сообщества</h2>
            <p className="epic-section-desc">
              Объявления, работа, жалобы с фото, маршруты и подписка на новые объявления — напишите «Начать»
            </p>
          </div>
          <VkBotBanner />
        </div>
      </section>

      <VillageGallery />
    </div>
  );
}
