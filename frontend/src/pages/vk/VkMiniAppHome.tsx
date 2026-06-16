import { Link } from "react-router-dom";
import { useSiteInfo } from "@/hooks/useSiteInfo";

export function VkMiniAppHome() {
  const { info } = useSiteInfo();
  const configured = info?.vk_mini_app_ready;

  return (
    <div className="space-y-4">
      <div className="page-panel page-panel--gold">
        <h1 className="literary-title text-xl m-0">Пушкинские Горы</h1>
        <p className="text-sm text-muted-foreground mt-2 mb-0">
          Афиша, объявления соседей и обращения — в компактном приложении VK.
        </p>
      </div>
      {!configured && (
        <p className="text-sm literary-page-note m-0">
          Mini App в режиме предпросмотра. Для продакшена администратору нужно указать VK_APP_ID и VK_APP_SECRET на сервере.
        </p>
      )}
      <div className="grid gap-2">
        <Link to="/vk/events" className="literary-btn literary-btn--forest w-full no-underline text-center">
          📅 Афиша и кино
        </Link>
        <Link to="/vk/classifieds" className="literary-btn literary-btn--ghost w-full no-underline text-center">
          📋 Объявления
        </Link>
        <Link to="/vk/complaints" className="literary-btn literary-btn--ghost w-full no-underline text-center">
          ⚠️ Подать обращение
        </Link>
        <Link to="/vk/cabinet" className="literary-btn literary-btn--ghost w-full no-underline text-center">
          🪶 Мой кабинет
        </Link>
      </div>
    </div>
  );
}
