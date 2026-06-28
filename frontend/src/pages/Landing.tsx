import { LandingHeroCinema } from "@/components/landing/LandingHeroCinema";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { LandingAlbumSection, LandingQuickActions } from "@/components/landing";

export function Landing() {
  return (
    <div className="landing-epic">
      <LandingHeroCinema />

      <div className="landing-album" id="landing-content">
        <div className="landing-album-inner max-w-5xl mx-auto px-4">
          <LandingAlbumSection reveal>
            <TodayInVillage />
          </LandingAlbumSection>

          <LandingAlbumSection divider reveal>
            <UpcomingEvents variant="landing" />
          </LandingAlbumSection>

          <LandingAlbumSection divider reveal>
            <LandingQuickActions />
          </LandingAlbumSection>
        </div>
      </div>
    </div>
  );
}
