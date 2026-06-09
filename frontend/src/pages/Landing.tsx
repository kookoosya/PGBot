import { Link } from "react-router-dom";
import { PushkinVersesSection } from "@/components/PushkinVersesSection";
import { SeasonalTip } from "@/components/SeasonalTip";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { VkBotBanner } from "@/components/VkBotLink";
import { VillageGallery } from "@/components/VillageGallery";
import { WeatherWidgetDetailed } from "@/components/weather/WeatherWidgetDetailed";
import { BRAND } from "@/lib/branding";
import { HERO_VERSE, VILLAGE_PHOTOS } from "@/lib/pushkin";

const heroPhoto = VILLAGE_PHOTOS[0];

export function Landing() {
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
