import { LiteraryInlineLoader } from "@/components/literary";
import { VkOfflineBanner } from "@/vk/components/VkOfflineBanner";
import { useOnlineStatus } from "@/vk/hooks/useOnlineStatus";
import { useVkAuth } from "@/vk/VkAuthContext";
import { VkNavigationProvider, useVkNavigation } from "@/vk/VkNavigationContext";
import { VkClassifiedDetail } from "@/vk/pages/VkClassifiedDetail";
import { VkClassifiedsTab } from "@/vk/pages/VkClassifiedsTab";
import { VkEventDetail } from "@/vk/pages/VkEventDetail";
import { VkEventsTab } from "@/vk/pages/VkEventsTab";
import { VkIssuesTab } from "@/vk/pages/VkIssuesTab";

const TABS = [
  { id: "events" as const, label: "Афиша", icon: "📅" },
  { id: "classifieds" as const, label: "Объявления", icon: "📋" },
  { id: "issues" as const, label: "Заявки", icon: "⚠️" },
];

function VkAppShell() {
  const online = useOnlineStatus();
  const { loading, user } = useVkAuth();
  const { tab, detail, setTab, isDetailView } = useVkNavigation();

  const headerTitle =
    detail?.type === "event" ? "Афиша" : detail?.type === "classified" ? "Объявления" : TABS.find((t) => t.id === tab)?.label;

  return (
    <div className="vk-mini-app">
      <header className="vk-mini-header">
        <p className="vk-mini-eyebrow">Пушкинские Горы</p>
        <h1 className="vk-mini-title">{headerTitle || "Портал посёлка"}</h1>
        {user?.full_name && !isDetailView && <p className="vk-mini-user">{user.full_name}</p>}
      </header>

      <VkOfflineBanner online={online} />

      <main className="vk-mini-main">
        {loading && !detail ? (
          <LiteraryInlineLoader label="Подключаем VK…" compact />
        ) : detail?.type === "event" ? (
          <VkEventDetail eventId={detail.id} />
        ) : detail?.type === "classified" ? (
          <VkClassifiedDetail adId={detail.id} />
        ) : (
          <>
            {tab === "events" && <VkEventsTab />}
            {tab === "classifieds" && <VkClassifiedsTab />}
            {tab === "issues" && <VkIssuesTab />}
          </>
        )}
      </main>

      {!isDetailView && (
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
    <VkNavigationProvider>
      <VkAppShell />
    </VkNavigationProvider>
  );
}
