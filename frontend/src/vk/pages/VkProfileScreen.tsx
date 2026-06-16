import { LiterarySectionHead } from "@/components/literary";
import { VkBackBar } from "@/vk/components/VkBackBar";
import { useVkAuth } from "@/vk/VkAuthContext";
import { useVkNavigation } from "@/vk/VkNavigationContext";

export function VkProfileScreen() {
  const { goBack, openHelp } = useVkNavigation();
  const { user, refreshAuth, logout } = useVkAuth();

  return (
    <section className="vk-tab-panel vk-screen-enter">
      <VkBackBar title="Профиль" onBack={goBack} />

      <article className="page-panel page-panel--gold">
        <LiterarySectionHead kicker="👤 Житель" title={user?.full_name || "Гость"} />

        <dl className="vk-profile-facts">
          {user?.phone && (
            <>
              <dt>Телефон</dt>
              <dd>{user.phone}</dd>
            </>
          )}
          <dt>Роль</dt>
          <dd>{user?.role === "resident" ? "Житель" : user?.role || "—"}</dd>
          <dt>Аккаунт VK</dt>
          <dd>Привязан к мини-приложению</dd>
        </dl>

        <div className="vk-profile-actions">
          <button type="button" className="literary-btn literary-btn--ghost w-full" onClick={() => openHelp()}>
            Помощь и FAQ
          </button>
          <button type="button" className="literary-btn literary-btn--primary w-full" onClick={() => void refreshAuth()}>
            Обновить сессию VK
          </button>
          <button type="button" className="literary-btn literary-btn--ghost w-full text-sm" onClick={logout}>
            Выйти из сессии
          </button>
        </div>
      </article>
    </section>
  );
}
