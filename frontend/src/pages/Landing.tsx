import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PushkinVersesSection } from "@/components/PushkinVersesSection";
import { SeasonalTip } from "@/components/SeasonalTip";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { VkBotBanner } from "@/components/VkBotLink";
import { VillageGallery } from "@/components/VillageGallery";
import { WeatherWidgetCompact } from "@/components/weather/WeatherWidgetCompact";
import { BRAND } from "@/lib/branding";
import { api, type ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { HERO_VERSE, VILLAGE_PHOTOS } from "@/lib/pushkin";

const heroPhoto = VILLAGE_PHOTOS[0];

const usefulNearby = [
  { icon: "🗺", title: "Карта", desc: "Магазины, аптеки, НКЦ, такси и маршруты по Пушкиногорью", to: "/map", tone: "forest" },
  { icon: "📋", title: "Объявления", desc: "Дрова, услуги, продажа — бесплатно от соседей", to: "/classifieds", tone: "gold" },
  { icon: "💼", title: "Работа", desc: "Вакансии и подработка в посёлке", to: "/jobs", tone: "forest" },
  { icon: "📅", title: "Афиша", desc: "События в Пушкинских Горах и кино в Пскове", to: "/events", tone: "gold" },
  { icon: "🤖", title: "ИИ-помощник", desc: "Тексты, идеи и ответы о посёлке", to: "/ai", tone: "forest" },
  { icon: "⚠️", title: "Обращения", desc: "Дороги, ЖКХ, освещение — официальный канал", to: "/complaints", tone: "gold" },
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

            <div className="epic-weather-row">
              <WeatherWidgetCompact variant="inline" />
            </div>

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

      <section className="page-section max-w-5xl mx-auto px-4 literary-dashboard">
        <SeasonalTip />
        <TodayInVillage />
        <UpcomingEvents />
      </section>

      <section className="literary-album-section">
        <div className="page-section max-w-5xl mx-auto px-4">
          <div className="literary-section-head">
            <div>
              <p className="literary-kicker">🧭 Для жителей и гостей</p>
              <h2 className="literary-title">Полезное рядом</h2>
              <p className="literary-lead">
                Карта посёлка, объявления соседей, работа, афиша и обращения — всё, что нужно в Пушкиногорье.
              </p>
            </div>
          </div>
          <div className="literary-useful-grid">
            {usefulNearby.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`literary-useful-card literary-useful-card--${item.tone} animate-in`}
              >
                <span className="literary-useful-icon">{item.icon}</span>
                <h3 className="literary-useful-title">{item.title}</h3>
                <p className="literary-useful-desc">{item.desc}</p>
                <span className="literary-useful-go">Открыть →</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="epic-jobs-section literary-album-section">
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
