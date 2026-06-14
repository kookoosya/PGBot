import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PushkinVersesSection } from "@/components/PushkinVersesSection";
import { SeasonalTip } from "@/components/SeasonalTip";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { VkBotBanner } from "@/components/VkBotLink";
import { VillageGallery } from "@/components/VillageGallery";
import { WeatherWidgetDetailed } from "@/components/weather/WeatherWidgetDetailed";
import { BRAND } from "@/lib/branding";
import { api, type ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { HERO_VERSE, VILLAGE_PHOTOS } from "@/lib/pushkin";

const heroPhoto = VILLAGE_PHOTOS[0];

const highlights = [
  { n: "01", icon: "🗺", title: "Карта", desc: "Магазины, такси, музеи и туристические маршруты по Пушкиногорью", to: "/map", tone: "sky" },
  { n: "02", icon: "📋", title: "Объявления", desc: "Дрова, услуги, продажа — бесплатно, без регистрации", to: "/classifieds", tone: "gold" },
  { n: "03", icon: "💼", title: "Работа", desc: "Вакансии и подработка от местных работодателей", to: "/jobs", tone: "emerald" },
  { n: "04", icon: "📅", title: "Афиша", desc: "Концерты, праздники, кино в Пушкинских Горах и Пскове", to: "/events", tone: "rose" },
  { n: "05", icon: "🤖", title: "ИИ-помощник", desc: "30 сообщений в день — тексты, идеи, ответы о посёлке", to: "/ai", tone: "violet" },
  { n: "06", icon: "⚠️", title: "Жалобы", desc: "Дороги, ЖКХ, освещение — официальный канал для жителей", to: "/complaints", tone: "forest" },
];

export function Landing() {
  const [jobAds, setJobAds] = useState<ClassifiedAd[]>([]);

  useEffect(() => {
    api
      .getClassifieds({ jobs_only: "true", page_size: "4" })
      .then((r) => setJobAds(r.items))
      .catch(() => {});
  }, []);

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

        <div className="epic-hero-inner epic-hero-inner-centered">
          <div className="epic-hero-copy animate-hero">
            <span className="epic-kicker">🪶 {BRAND.district}</span>
            <blockquote className="epic-quote">{HERO_VERSE}</blockquote>
            <h1 className="epic-title">
              <span className="epic-title-line">{BRAND.name}</span>
              <span className="epic-title-sub">{BRAND.tagline}</span>
            </h1>
            <p className="epic-lead">{BRAND.description}</p>

            <div className="epic-cta-row">
              <Link to="/map" className="epic-btn epic-btn-primary epic-btn-lg">
                🗺 Открыть карту
              </Link>
              <Link to="/events" className="epic-btn epic-btn-glass epic-btn-lg">
                📅 Афиша событий
              </Link>
              <Link to="/classifieds" className="epic-btn epic-btn-glass epic-btn-lg">
                📋 Объявления
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="page-section max-w-5xl mx-auto px-4 village-dashboard">
        <WeatherWidgetDetailed />
        <SeasonalTip />
        <TodayInVillage />
        <UpcomingEvents />
      </section>

      <section className="epic-bento-section">
        <div className="page-section">
          <div className="epic-section-head">
            <p className="epic-section-kicker">Всё в одном месте</p>
            <h2 className="epic-section-title">Портал для жителей и гостей</h2>
            <p className="epic-section-desc">
              Карта, объявления, работа, афиша, услуги и ИИ — на сайте и в VK-боте
            </p>
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
                Местные работодатели — без посредников. Разместить вакансию можно бесплатно.
              </p>
            </div>
            <Link to="/jobs" className="epic-btn epic-btn-primary">
              Все вакансии
            </Link>
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
                    <p className="epic-job-desc">
                      {ad.description.slice(0, 120)}
                      {ad.description.length > 120 ? "…" : ""}
                    </p>
                    {ad.price != null && (
                      <p className="epic-job-pay">
                        {ad.price} {ad.price_unit || "₽"}
                      </p>
                    )}
                  </div>
                </Link>
              );
            })}
            {jobAds.length === 0 && (
              <div className="epic-job-empty">
                <p>Пока нет опубликованных вакансий.</p>
                <Link to="/jobs" className="epic-btn epic-btn-glass">
                  Разместить первую
                </Link>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="epic-vk-section">
        <div className="page-section max-w-3xl mx-auto">
          <div className="epic-section-head mb-6">
            <p className="epic-section-kicker">В VK тоже</p>
            <h2 className="epic-section-title">Бот в сообщениях сообщества</h2>
            <p className="epic-section-desc">
              Объявления, работа, жалобы с фото, маршруты и подписка — напишите «Начать»
            </p>
          </div>
          <VkBotBanner />
        </div>
      </section>

      <PushkinVersesSection />
      <VillageGallery />
    </div>
  );
}
