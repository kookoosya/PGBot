import { LiterarySectionHead } from "@/components/literary";
import { VkBackBar } from "@/vk/components/VkBackBar";
import { useVkNavigation } from "@/vk/VkNavigationContext";

const FAQ = [
  {
    q: "Как подать объявление?",
    a: "Откройте вкладку «Объявления», нажмите «Подать объявление» и заполните форму. После модерации оно появится в списке.",
  },
  {
    q: "Как отправить обращение?",
    a: "На вкладке «Заявки» опишите проблему и отправьте форму. Статус и ответы администрации видны в карточке обращения.",
  },
  {
    q: "Почему не загружается афиша?",
    a: "Проверьте интернет. При медленной сети приложение повторит запрос автоматически.",
  },
  {
    q: "Сессия истекла — что делать?",
    a: "Нажмите «Войти снова» или «Обновить сессию VK» в профиле. Закройте и откройте мини-приложение из ВКонтакте.",
  },
];

export function VkHelpScreen() {
  const { goBack } = useVkNavigation();

  return (
    <section className="vk-tab-panel vk-screen-enter">
      <VkBackBar title="Помощь" onBack={goBack} />

      <LiterarySectionHead kicker="🪶 Справка" title="Частые вопросы" lead="Коротко о возможностях портала." />

      <div className="vk-faq-list">
        {FAQ.map((item) => (
          <details key={item.q} className="vk-faq-item">
            <summary>{item.q}</summary>
            <p>{item.a}</p>
          </details>
        ))}
      </div>

      <p className="text-xs text-muted-foreground m-0">
        Полная версия портала доступна на сайте посёлка. По срочным вопросам — через сообщество ВКонтакте.
      </p>
    </section>
  );
}
