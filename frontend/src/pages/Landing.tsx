import { LandingHeroCinema } from "@/components/landing/LandingHeroCinema";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { LandingAlbumSection, LandingQuickActions } from "@/components/landing";
import { LandingClosingStrip } from "@/components/landing/LandingExtras";

export function Landing() {
  return (
    <div className="landing-epic">
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

          <LandingClosingStrip />
        </div>
      </div>
    </div>
  );
}
