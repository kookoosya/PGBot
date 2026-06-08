import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { VillageGallery } from "@/components/VillageGallery";
import { VkBotLink } from "@/components/VkBotLink";
import { BRAND } from "@/lib/branding";
import { MAIN_SECTIONS } from "@/lib/navigation";
import { api } from "@/lib/api";
import { VILLAGE_PHOTOS } from "@/lib/pushkin";

const heroPhoto = VILLAGE_PHOTOS[0];

export function Landing() {
  const [placesCount, setPlacesCount] = useState<number | null>(null);

  useEffect(() => {
    api.getMapStats().then((s) => setPlacesCount(s.total_places)).catch(() => {});
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
            <h1 className="epic-title">
              <span className="epic-title-line">{BRAND.name}</span>
              <span className="epic-title-sub">{BRAND.tagline}</span>
            </h1>
            <p className="epic-lead">{BRAND.description}</p>
            {placesCount != null && (
              <p className="epic-hero-meta">
                {placesCount} организаций на карте · объявления и вакансии бесплатно
              </p>
            )}

            <div className="epic-cta-row">
              <Link to="/map" className="epic-btn epic-btn-primary">🗺 Карта посёлка</Link>
              <Link to="/classifieds" className="epic-btn epic-btn-glass">📋 Объявления</Link>
            </div>
          </div>

          <div className="epic-hero-panel animate-in">
            <p className="epic-panel-label">Разделы</p>
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

      <VillageGallery />
    </div>
  );
}
