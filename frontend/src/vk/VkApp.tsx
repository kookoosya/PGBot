import { VkErrorBoundary } from "@/vk/components/VkErrorBoundary";
import { VkOfflineBanner } from "@/vk/components/VkOfflineBanner";
import { VkSkeletonDetail } from "@/vk/components/VkSkeleton";
import { useOnlineStatus } from "@/vk/hooks/useOnlineStatus";
import { useVkAuth } from "@/vk/VkAuthContext";
import { VkNavigationProvider, useVkNavigation } from "@/vk/VkNavigationContext";
import { VkClassifiedDetail } from "@/vk/pages/VkClassifiedDetail";
import { VkClassifiedsTab } from "@/vk/pages/VkClassifiedsTab";
import { VkEventDetail } from "@/vk/pages/VkEventDetail";
import { VkEventsTab } from "@/vk/pages/VkEventsTab";
import { VkHelpScreen } from "@/vk/pages/VkHelpScreen";
import { VkIssueDetail } from "@/vk/pages/VkIssueDetail";
import { VkIssuesTab } from "@/vk/pages/VkIssuesTab";
import { VkProfileScreen } from "@/vk/pages/VkProfileScreen";

const TABS = [
  { id: "events" as const, label: "Афиша", icon: "📅" },
  { id: "classifieds" as const, label: "Объявления", icon: "📋" },
  { id: "issues" as const, label: "Заявки", icon: "⚠️" },
];

function screenTitle(current: ReturnType<typeof useVkNavigation>["current"], tab: string): string {
  if (current.type === "event") return "Афиша";
  if (current.type === "classified") return "Объявления";
  if (current.type === "issue") return "Заявки";
  if (current.type === "profile") return "Профиль";
  if (current.type === "help") return "Помощь";
  return TABS.find((t) => t.id === tab)?.label || "Портал посёлка";
}

function VkScreenRouter() {
  const { current, tab } = useVkNavigation();

  if (current.type === "event") return <VkEventDetail eventId={current.id} />;
  if (current.type === "classified") return <VkClassifiedDetail adId={current.id} />;
  if (current.type === "issue") return <VkIssueDetail issueId={current.id} />;
  if (current.type === "profile") return <VkProfileScreen />;
  if (current.type === "help") return <VkHelpScreen />;

  return (
    <>
      {tab === "events" && <VkEventsTab />}
      {tab === "classifieds" && <VkClassifiedsTab />}
      {tab === "issues" && <VkIssuesTab />}
    </>
  );
}

function VkAppShell() {
  const online = useOnlineStatus();
  const { loading, user } = useVkAuth();
  const { tab, current, setTab, openProfile, openHelp, isDetailView, isOverlayView } = useVkNavigation();

  const headerTitle = screenTitle(current, tab);
  const showNav = !isDetailView && !isOverlayView;

  return (
    <div className="vk-mini-app">
      <header className="vk-mini-header">
        <div className="vk-mini-header-row">
          <div>
            <p className="vk-mini-eyebrow">Пушкинские Горы</p>
            <h1 className="vk-mini-title">{headerTitle}</h1>
            {user?.full_name && showNav && <p className="vk-mini-user">{user.full_name}</p>}
          </div>
          {showNav && (
            <div className="vk-mini-header-actions">
              <button type="button" className="vk-header-icon-btn" onClick={openHelp} aria-label="Помощь">
                ?
              </button>
              <button type="button" className="vk-header-icon-btn" onClick={openProfile} aria-label="Профиль">
                👤
              </button>
            </div>
          )}
        </div>
      </header>

      <VkOfflineBanner online={online} />

      <main className={`vk-mini-main${isDetailView || isOverlayView ? " vk-mini-main--detail" : ""}`}>
        {loading && current.type === "tab" ? (
          <VkSkeletonDetail />
        ) : (
          <div key={current.type === "tab" ? tab : `${current.type}-${"id" in current ? current.id : current.type}`} className="vk-screen-enter">
            <VkScreenRouter />
          </div>
        )}
      </main>

      {showNav && (
        <nav className="vk-mini-nav" aria-label="Разделы мини-приложения">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`vk-mini-nav-btn${tab === item.id ? " vk-mini-nav-btn--active" : ""}`}
              onClick={() => setTab(item.id)}
            >
              <span className="vk-mini-nav-icon" aria-hidden>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      )}
    </div>
  );
}

export function VkApp() {
  return (
    <VkErrorBoundary>
      <VkNavigationProvider>
        <VkAppShell />
      </VkNavigationProvider>
    </VkErrorBoundary>
  );
}
