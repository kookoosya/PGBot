import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { BRAND } from "@/lib/branding";

/** Заглушка VK Mini App — полноценный клиент после регистрации приложения в VK. */
export function VkMiniAppPage() {
  return (
    <div className="literary-page page-section max-w-lg mx-auto py-8">
      <PageHeader
        icon="📱"
        title="Приложение ВКонтакте"
        subtitle="Компактный портал посёлка внутри VK — афиша, объявления и обращения."
      />
      <div className="page-panel page-panel--gold space-y-4">
        <p className="m-0 text-base">
          Mini App подключается после создания приложения в кабинете VK. Пока пользуйтесь сайтом или напишите боту «Начать» в сообщениях сообщества.
        </p>
        <div className="flex flex-wrap gap-2">
          <Link to="/events" className="literary-btn literary-btn--forest no-underline">
            📅 Афиша
          </Link>
          <Link to="/classifieds" className="literary-btn literary-btn--ghost no-underline">
            📋 Объявления
          </Link>
          <Link to="/" className="literary-btn literary-btn--ghost no-underline">
            На главную
          </Link>
        </div>
        <p className="text-xs text-muted-foreground m-0">
          {BRAND.name} · веб-версия: sslip.io
        </p>
      </div>
    </div>
  );
}
