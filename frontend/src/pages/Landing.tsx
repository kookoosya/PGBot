import { PushkinVersesSection } from "@/components/PushkinVersesSection";
import { SeasonalTip } from "@/components/SeasonalTip";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { VkBotBanner } from "@/components/VkBotLink";
import { VillageGallery } from "@/components/VillageGallery";
import { WeatherWidgetCompact } from "@/components/weather/WeatherWidgetCompact";
import { LiterarySectionHead } from "@/components/literary";
import {
  LandingAlbumSection,
  LandingJobsPreview,
  LandingUsefulNearby,
} from "@/components/landing";
import { BRAND } from "@/lib/branding";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";
import { HERO_VERSE, VILLAGE_PHOTOS } from "@/lib/pushkin";
import { Link } from "react-router-dom";

const heroPhoto = VILLAGE_PHOTOS[0];
const vkCopy = LANDING_SECTIONS.vk;

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

      <div className="landing-album">
        <div className="landing-album-inner max-w-5xl mx-auto px-4">
          <LandingAlbumSection>
            <div className="landing-today">
              <SeasonalTip />
              <TodayInVillage />
            </div>
          </LandingAlbumSection>

          <LandingAlbumSection divider>
            <UpcomingEvents variant="landing" />
          </LandingAlbumSection>

          <LandingAlbumSection divider>
            <LandingJobsPreview />
          </LandingAlbumSection>

          <LandingAlbumSection divider>
            <LandingUsefulNearby />
          </LandingAlbumSection>

          <LandingAlbumSection divider id="vk">
            <div className="page-panel landing-block landing-vk-panel">
              <LiterarySectionHead
                kicker={vkCopy.kicker}
                title={vkCopy.title}
                lead={vkCopy.lead}
              />
              <VkBotBanner />
            </div>
          </LandingAlbumSection>
        </div>
      </div>

      <PushkinVersesSection />
      <VillageGallery />
    </div>
  );
}
