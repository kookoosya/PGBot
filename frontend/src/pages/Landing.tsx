import { FestivalHeroBanner } from "@/components/FestivalHeroBanner";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { WeatherWidgetCompact } from "@/components/weather/WeatherWidgetCompact";
import { LandingAlbumSection, LandingQuickActions } from "@/components/landing";
import { LandingEventsCta } from "@/components/landing/LandingEventsCta";
import { BRAND } from "@/lib/branding";
import { LANDING_HERO } from "@/lib/literaryCopy";
import { VILLAGE_PHOTOS } from "@/lib/villagePhotos";
import { Link } from "react-router-dom";

const heroPhoto = VILLAGE_PHOTOS[0];
const heroCopy = LANDING_HERO;

export function Landing() {
  return (
    <div className="landing-epic">
      <section className="epic-hero epic-hero--literary">
        <div className="epic-hero-bg" aria-hidden>
          <picture>
            <source srcSet={heroPhoto.webp} type="image/webp" />
            <img
              src={heroPhoto.url}
              alt=""
              className="epic-hero-photo"
              width={1600}
              height={900}
              decoding="async"
              fetchPriority="high"
            />
          </picture>
          <div className="epic-hero-scrim" />
          <div className="epic-hero-vignette" />
          <div className="epic-hero-mesh" />
        </div>

        <div className="epic-hero-weather-corner" aria-label="Погода">
          <WeatherWidgetCompact variant="inline" />
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

              <div className="epic-cta-row epic-cta-row--primary">
                <Link to="/map" className="epic-btn epic-btn-primary epic-btn-lg">
                  🗺 {heroCopy.ctaMap}
                </Link>
                <LandingEventsCta defaultLabel={heroCopy.ctaEvents} />
              </div>
              <FestivalHeroBanner />
            </div>
          </div>
        </div>
      </section>

      <div className="landing-album">
        <div className="landing-album-inner max-w-5xl mx-auto px-4">
          <LandingAlbumSection>
            <TodayInVillage />
          </LandingAlbumSection>

          <LandingAlbumSection divider>
            <UpcomingEvents variant="landing" />
          </LandingAlbumSection>

          <LandingAlbumSection divider>
            <LandingQuickActions />
          </LandingAlbumSection>
        </div>
      </div>
    </div>
  );
}
