import { useState } from "react";
import { LiteraryInlineLoader } from "@/components/literary";
import { useVkAuth } from "@/vk/VkAuthContext";
import { VkClassifiedsTab } from "@/vk/pages/VkClassifiedsTab";
import { VkEventsTab } from "@/vk/pages/VkEventsTab";
import { VkIssuesTab } from "@/vk/pages/VkIssuesTab";

type VkTab = "events" | "classifieds" | "issues";

const TABS: { id: VkTab; label: string; icon: string }[] = [
  { id: "events", label: "Афиша", icon: "📅" },
  { id: "classifieds", label: "Объявления", icon: "📋" },
  { id: "issues", label: "Заявки", icon: "⚠️" },
];

export function VkApp() {
  const [tab, setTab] = useState<VkTab>("events");
  const { loading, user } = useVkAuth();

  return (
    <div className="vk-mini-app">
      <header className="vk-mini-header">
        <p className="vk-mini-eyebrow">Пушкинские Горы</p>
        <h1 className="vk-mini-title">Портал посёлка</h1>
        {user?.full_name && <p className="vk-mini-user">{user.full_name}</p>}
      </header>

      <main className="vk-mini-main">
        {loading && tab !== "issues" ? (
          <LiteraryInlineLoader label="Подключаем VK…" compact />
        ) : (
          <>
            {tab === "events" && <VkEventsTab />}
            {tab === "classifieds" && <VkClassifiedsTab />}
            {tab === "issues" && <VkIssuesTab />}
          </>
        )}
      </main>

      <nav className="vk-mini-nav" aria-label="Разделы мини-приложения">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`vk-mini-nav-btn${tab === item.id ? " vk-mini-nav-btn--active" : ""}`}
            onClick={() => setTab(item.id)}
          >
            <span aria-hidden>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
