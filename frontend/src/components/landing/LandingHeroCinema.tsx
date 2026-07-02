import { FestivalHeroBanner } from "@/components/FestivalHeroBanner";
import { LandingEventsCta } from "@/components/landing/LandingEventsCta";
import { WeatherWidgetCompact } from "@/components/weather/WeatherWidgetCompact";
import { BRAND } from "@/lib/branding";
import { LANDING_HERO } from "@/lib/literaryCopy";
import { VILLAGE_PHOTOS } from "@/lib/villagePhotos";
import { Link } from "react-router-dom";

const heroPhotos = [VILLAGE_PHOTOS[0], VILLAGE_PHOTOS[1]];
const heroCopy = LANDING_HERO;

function HeroPhotoLayer({ photo, className }: { photo: (typeof VILLAGE_PHOTOS)[0]; className: string }) {
  return (
    <picture className={className}>
      <source srcSet={photo.webp} type="image/webp" />
      <img
        src={photo.url}
        alt=""
        className="epic-hero-photo"
        width={1600}
        height={900}
        decoding="async"
        fetchPriority={className.includes("--a") ? "high" : "low"}
      />
    </picture>
  );
}

/** Кинематографичный hero главной — crossfade, зерно, цитата, scroll hint. */
export function LandingHeroCinema() {
  return (
    <section className="epic-hero epic-hero--literary epic-hero--cinema">
      <div className="epic-hero-bg" aria-hidden>
        <HeroPhotoLayer photo={heroPhotos[0]} className="epic-hero-photo-layer epic-hero-photo-layer--a" />
        <HeroPhotoLayer photo={heroPhotos[1]} className="epic-hero-photo-layer epic-hero-photo-layer--b" />
        <div className="epic-hero-scrim" />
        <div className="epic-hero-vignette" />
        <div className="epic-hero-mesh" />
        <div className="epic-hero-grain" />
        <div className="epic-hero-rays" />
        <div className="hero-glow" />
      </div>

      <div className="epic-hero-feathers" aria-hidden>
        <span className="epic-feather epic-feather--1">🪶</span>
        <span className="epic-feather epic-feather--2">🪶</span>
        <span className="epic-feather epic-feather--3">🪶</span>
      </div>

      <div className="epic-hero-weather-corner" aria-label="Погода">
        <WeatherWidgetCompact variant="inline" />
      </div>

      <div className="epic-hero-inner epic-hero-inner-centered">
        <div className="epic-hero-copy epic-hero-copy--literary animate-hero animate-hero-cinema">
          <div className="epic-hero-plate">
            <span className="epic-kicker epic-kicker--cinema">🪶 {heroCopy.kicker}</span>

            <blockquote className="epic-quote epic-quote--cinema">
              «{heroCopy.quote}»
              <cite className="epic-quote-source">
                — {heroCopy.quoteSource}
                {heroCopy.quoteWork ? `, «${heroCopy.quoteWork}»` : ""}
                {heroCopy.quoteYear ? `, ${heroCopy.quoteYear}` : ""}
              </cite>
            </blockquote>

            <div className="epic-hero-ornament" aria-hidden />

            <h1 className="epic-title">
              <span className="epic-title-line epic-title-line--cinema">{BRAND.name}</span>
              <span className="epic-title-sub">{heroCopy.tagline}</span>
            </h1>

            <p className="epic-lead epic-lead--short">{heroCopy.lead}</p>

            <div className="epic-cta-row epic-cta-row--primary">
              <Link to="/map" className="epic-btn epic-btn-primary epic-btn-lg epic-btn-shine">
                🗺 {heroCopy.ctaMap}
              </Link>
              <LandingEventsCta defaultLabel={heroCopy.ctaEvents} />
            </div>

            <FestivalHeroBanner />
          </div>
        </div>
      </div>

      <a href="#landing-content" className="epic-scroll-hint" aria-label="К содержимому страницы">
        <span className="epic-scroll-hint-label">Листайте</span>
        <span className="epic-scroll-hint-arrow" aria-hidden>
          ↓
        </span>
      </a>

      <p className="epic-hero-caption" aria-hidden>
        {heroPhotos.map((p) => p.title).join(" · ")}
      </p>
    </section>
  );
}
