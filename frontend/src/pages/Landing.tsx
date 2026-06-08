import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PushkinVersesSection } from "@/components/PushkinVersesSection";
import { VkBotBanner } from "@/components/VkBotLink";
import { VillageGallery } from "@/components/VillageGallery";
import { WeatherWidgetCompact } from "@/components/weather/WeatherWidgetCompact";
import { WeatherWidgetDetailed } from "@/components/weather/WeatherWidgetDetailed";
import { BRAND } from "@/lib/branding";
import { api } from "@/lib/api";
import { HERO_VERSE, VILLAGE_PHOTOS } from "@/lib/pushkin";

const heroPhoto = VILLAGE_PHOTOS[0];

export function Landing() {
  const [placesCount, setPlacesCount] = useState<number | null>(null);

  useEffect(() => {
    api.getMapStats().then((s) => setPlacesCount(s.total_places)).catch(() => {});
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

            {placesCount != null && (
              <div className="epic-stats-row">
                <div className="epic-stat-card epic-stat-card-static">
                  <strong>{placesCount}</strong>
                  <span>организаций на карте</span>
                </div>
                <div className="epic-stat-card epic-stat-card-static">
                  <strong>0 ₽</strong>
                  <span>объявления и вакансии</span>
                </div>
                <div className="epic-stat-card epic-stat-card-static">
                  <strong>24/7</strong>
                  <span>ИИ и ВК-бот</span>
                </div>
              </div>
            )}

            <div className="epic-cta-row">
              <Link to="/map" className="epic-btn epic-btn-primary epic-btn-lg">
                🗺 Открыть карту
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="page-section max-w-5xl mx-auto px-4">
        <WeatherWidgetDetailed />
      </section>

      <section className="epic-vk-section">
        <div className="page-section max-w-2xl mx-auto">
          <VkBotBanner />
        </div>
      </section>

      <PushkinVersesSection />
      <VillageGallery />
    </div>
  );
}
