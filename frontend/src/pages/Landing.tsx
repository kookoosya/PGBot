import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { VkBotBanner } from "@/components/VkBotLink";
import { WeatherWidgetCompact } from "@/components/weather/WeatherWidgetCompact";
import { LiterarySectionHead } from "@/components/literary";
import { LandingAlbumSection, LandingQuickNav } from "@/components/landing";
import { BRAND } from "@/lib/branding";
import { LANDING_HERO, LANDING_SECTIONS } from "@/lib/literaryCopy";
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
              <h1 className="epic-title">
                <span className="epic-title-line">{BRAND.name}</span>
                <span className="epic-title-sub">{heroCopy.tagline}</span>
              </h1>
              <p className="epic-lead epic-lead--short">{heroCopy.lead}</p>

              <div className="epic-weather-row">
                <WeatherWidgetCompact variant="inline" />
              </div>

              <div className="epic-cta-row epic-cta-row--primary">
                <Link to="/map" className="epic-btn epic-btn-primary epic-btn-lg">
                  🗺 {heroCopy.ctaMap}
                </Link>
                <Link to="/events" className="epic-btn epic-btn-glass epic-btn-lg">
                  📅 {heroCopy.ctaEvents}
                </Link>
              </div>
              <p className="epic-hero-more">
                <Link to="/classifieds" className="epic-hero-more-link">
                  📋 {heroCopy.ctaClassifieds} →
                </Link>
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className="landing-album">
        <div className="landing-album-inner max-w-5xl mx-auto px-4">
          <LandingAlbumSection>
            <LandingQuickNav />
          </LandingAlbumSection>

          <LandingAlbumSection divider>
            <TodayInVillage />
          </LandingAlbumSection>

          <LandingAlbumSection divider>
            <UpcomingEvents variant="landing" />
          </LandingAlbumSection>

          <LandingAlbumSection divider id="vk">
            <div className="page-panel landing-block landing-vk-panel">
              <LiterarySectionHead
                kicker={vkCopy.kicker}
                title={vkCopy.title}
                lead={vkCopy.lead}
                compact
              />
              <VkBotBanner hidePortalChips />
            </div>
          </LandingAlbumSection>

          <blockquote className="landing-album-closing-verse" cite="Пушкин">
            {HERO_VERSE}
          </blockquote>
        </div>
      </div>
    </div>
  );
}
