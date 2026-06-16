import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { useSiteInfo } from "@/hooks/useSiteInfo";
import { CTA } from "@/lib/cta";

/** Заглушка VK Mini App — полноценный клиент после регистрации приложения в VK. */
export function VkMiniAppPage() {
  const { siteUrl } = useSiteInfo();
  const siteLabel = (() => {
    try {
      return new URL(siteUrl).host;
    } catch {
      return "портал";
    }
  })();

  return (
    <div className="literary-page page-section max-w-lg mx-auto py-8">
      <PageHeader
        icon="📱"
        title="Приложение ВКонтакте"
        subtitle="Компактная версия портала внутри VK: афиша, объявления и обращения."
      />
      <div className="page-panel page-panel--gold space-y-4">
        <p className="m-0 text-base">
          Mini App подключается после создания приложения в кабинете VK. Пока используйте сайт или напишите боту «Начать» в сообщениях сообщества.
        </p>
        <div className="flex flex-wrap gap-2">
          <Link to="/events" className="literary-btn literary-btn--forest no-underline">
            📅 Афиша
          </Link>
          <Link to="/classifieds" className="literary-btn literary-btn--ghost no-underline">
            📋 Объявления
          </Link>
          <Link to="/" className="literary-btn literary-btn--ghost no-underline">
            {CTA.backHome}
          </Link>
        </div>
        <p className="text-xs text-muted-foreground m-0">
          Веб-версия: {siteLabel}
        </p>
      </div>
    </div>
  );
}
