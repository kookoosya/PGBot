import { FormEvent, useState } from "react";
import { useLocation } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useUserAuth } from "@/lib/userAuth";

const ideas = [
  "Добавить расписание автобусов",
  "Уведомления о новых объявлениях",
  "Фотоотчёты по жалобам",
  "Календарь мероприятий посёлка",
  "Раздел для туристов",
];

export function Wishes() {
  const { user } = useUserAuth();
  const location = useLocation();
  const [message, setMessage] = useState("");
  const [contact, setContact] = useState(user?.phone || user?.email || "");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.submitFeedback({
        message: message.trim(),
        contact: contact.trim() || undefined,
        page: location.pathname,
      });
      setSent(true);
      setMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось отправить");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-section">
      <PageHeader
        icon="💡"
        title="Пожелания"
        subtitle="Предложите, как сделать портал лучше — идеи увидит администратор"
      />

      {sent ? (
        <div className="epic-bento-card epic-bento-emerald max-w-xl mx-auto text-center p-8">
          <p className="text-4xl mb-3">✨</p>
          <h2 className="text-xl font-bold m-0">Спасибо!</h2>
          <p className="text-muted-foreground mt-2 mb-4">Ваше пожелание принято. Мы учтём его при развитии портала.</p>
          <Button onClick={() => setSent(false)}>Отправить ещё</Button>
        </div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[1fr_320px] max-w-5xl mx-auto">
          <form onSubmit={submit} className="pushkin-card p-6 md:p-8 space-y-4 form-glow">
            <label className="block text-sm font-semibold">
              Ваше пожелание или идея
              <textarea
                className="mt-2 w-full min-h-[160px] rounded-xl border px-4 py-3 text-sm"
                placeholder="Опишите, что улучшить на сайте, какой раздел добавить, что неудобно..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
                minLength={5}
                maxLength={4000}
              />
            </label>
            <label className="block text-sm font-semibold">
              Контакт (необязательно)
              <input
                className="mt-2 w-full rounded-xl border px-4 py-2.5 text-sm"
                placeholder="Телефон, VK или email — чтобы уточнить детали"
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                maxLength={200}
              />
            </label>
            {error && <p className="alert-error">{error}</p>}
            <Button type="submit" disabled={loading || message.trim().length < 5} className="w-full md:w-auto">
              {loading ? "Отправляю…" : "Отправить пожелание"}
            </Button>
          </form>

          <aside className="space-y-4">
            <div className="pushkin-card p-5">
              <h3 className="font-bold m-0 mb-2">Примеры идей</h3>
              <div className="suggest-chips">
                {ideas.map((idea) => (
                  <button
                    key={idea}
                    type="button"
                    className="suggest-chip"
                    onClick={() => setMessage((m) => (m ? `${m}\n${idea}` : idea))}
                  >
                    {idea}
                  </button>
                ))}
              </div>
            </div>
            <div className="pushkin-card p-5 text-sm text-muted-foreground">
              Пожелания помогают развивать портал для жителей и гостей Пушкинских Гор. Можно писать про дизайн, карту, объявления, жалобы и VK-бота.
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
