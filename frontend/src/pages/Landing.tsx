import { LandingHeroCinema } from "@/components/landing/LandingHeroCinema";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { LandingAlbumSection, LandingQuickActions, LandingVkPromo } from "@/components/landing";
import { LandingClosingStrip } from "@/components/landing/LandingClosingStrip";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";

export function Landing() {
  useDocumentTitle();

  return (    <div className="landing-epic">
      <LandingHeroCinema />

      <div className="landing-album landing-album--cinema" id="landing-content">
        <div className="landing-album-inner landing-album-inner--wide mx-auto px-4">
          <LandingAlbumSection reveal>
            <TodayInVillage />
          </LandingAlbumSection>

          <LandingAlbumSection divider reveal>
            <UpcomingEvents variant="landing" />
          </LandingAlbumSection>

          <LandingAlbumSection divider reveal>
            <LandingQuickActions />
          </LandingAlbumSection>

          <LandingAlbumSection divider reveal>
            <LandingVkPromo />
          </LandingAlbumSection>

          <LandingClosingStrip />
        </div>
      </div>
    </div>
  );
}
