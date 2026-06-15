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
import { LANDING_HERO, LANDING_SECTIONS, LITERARY_VERSES } from "@/lib/literaryCopy";
import { HERO_VERSE, VILLAGE_PHOTOS } from "@/lib/pushkin";
import { Link } from "react-router-dom";

const heroPhoto = VILLAGE_PHOTOS[0];
const vkCopy = LANDING_SECTIONS.vk;
const heroCopy = LANDING_HERO;

export function Landing() {
  return (
    <div className="landing-epic">
      <section className="epic-hero epic-hero--literary">
        <div className="epic-hero-bg" aria-hidden>
          <picture>
            <source srcSet={heroPhoto.webp} type="image/webp" />
            <img src={heroPhoto.url} alt="" className="epic-hero-photo" />
          </picture>
          <div className="epic-hero-scrim" />
          <div className="epic-hero-vignette" />
          <div className="epic-hero-mesh" />
        </div>

        <div className="epic-hero-inner epic-hero-inner-centered">
          <div className="epic-hero-copy epic-hero-copy--literary animate-hero">
            <div className="epic-hero-plate">
              <span className="epic-kicker">🪶 {heroCopy.kicker}</span>
              <blockquote className="epic-quote" cite="Пушкин">
                {HERO_VERSE}
              </blockquote>
              <div className="epic-hero-ornament" aria-hidden />
              <h1 className="epic-title">
                <span className="epic-title-line">{BRAND.name}</span>
                <span className="epic-title-sub">{heroCopy.tagline}</span>
              </h1>
              <p className="epic-lead">{heroCopy.lead}</p>

              <div className="epic-weather-row">
                <WeatherWidgetCompact variant="inline" />
              </div>

              <div className="epic-cta-row">
                <Link to="/map" className="epic-btn epic-btn-primary epic-btn-lg">
                  🗺 {heroCopy.ctaMap}
                </Link>
                <Link to="/events" className="epic-btn epic-btn-glass epic-btn-lg">
                  📅 {heroCopy.ctaEvents}
                </Link>
                <Link to="/classifieds" className="epic-btn epic-btn-glass epic-btn-lg">
                  📋 {heroCopy.ctaClassifieds}
                </Link>
              </div>
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

          <p className="landing-album-closing-verse" aria-hidden>
            {LITERARY_VERSES.landing}
          </p>
        </div>
      </div>

      <PushkinVersesSection />
      <VillageGallery />
    </div>
  );
}
