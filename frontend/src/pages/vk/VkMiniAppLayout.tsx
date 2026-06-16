import { NavLink, Outlet } from "react-router-dom";
import { LiteraryInlineLoader } from "@/components/literary";
import { useVkMiniApp } from "@/hooks/useVkMiniApp";

const TABS = [
  { to: "/vk", label: "🏠 Главная", end: true },
  { to: "/vk/events", label: "📅 Афиша" },
  { to: "/vk/classifieds", label: "📋 Объявления" },
  { to: "/vk/complaints", label: "⚠️ Обращения" },
  { to: "/vk/cabinet", label: "🪶 Кабинет" },
] as const;

/** Compact shell for VK Mini App — no site header/footer. */
export function VkMiniAppLayout() {
  const { loading, error, inVk } = useVkMiniApp();

  return (
    <div className="vk-mini-app min-h-screen flex flex-col bg-background">
      <main className="flex-1 overflow-y-auto px-3 py-4 max-w-lg mx-auto w-full">
        {loading && <LiteraryInlineLoader label="Подключаем VK…" />}
        {!loading && error && (
          <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">
            {error}
          </p>
        )}
        {!loading && !inVk && (
          <p className="text-sm text-muted-foreground mb-4">
            Откройте через приложение ВКонтакте или используйте веб-версию портала.
          </p>
        )}
        <Outlet />
      </main>
      <nav className="vk-mini-tabs border-t border-border bg-card/95 backdrop-blur sticky bottom-0">
        <div className="max-w-lg mx-auto grid grid-cols-5 gap-1 px-1 py-2">
          {TABS.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={"end" in tab ? tab.end : false}
              className={({ isActive }) =>
                `vk-mini-tab text-center text-[10px] leading-tight py-1 px-0.5 rounded-md no-underline${
                  isActive ? " vk-mini-tab--active" : ""
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
