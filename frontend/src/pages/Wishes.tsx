import { FormEvent, useState } from "react";
import { useLocation } from "react-router-dom";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { api } from "@/lib/api";
import { EMPTY_STATES, LITERARY_VERSES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useUserAuth } from "@/lib/userAuth";

const copy = PAGE_SECTIONS.wishes;

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
    <div className="literary-page page-section max-w-5xl">
      <LiterarySectionHead kicker={copy.kicker} title={copy.title} lead={copy.lead} />

      {sent ? (
        <LiteraryEmptyState {...EMPTY_STATES.wishesSent}>
          <button
            type="button"
            className="literary-btn literary-btn--ghost mt-3"
            onClick={() => setSent(false)}
          >
            Отправить ещё
          </button>
        </LiteraryEmptyState>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[1fr_300px] mt-6">
          <form onSubmit={submit} className="page-panel page-panel--forest literary-auth-panel space-y-4">
            <label className="block text-sm font-semibold">
              Ваше пожелание или идея
              <textarea
                className="mt-2 w-full min-h-[160px] rounded-lg border px-4 py-3 text-sm pushkin-select"
                placeholder="Опишите, что улучшить на сайте, какой раздел добавить, что неудобно…"
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
                className="mt-2 w-full rounded-lg border px-4 py-2.5 text-sm pushkin-select"
                placeholder="Телефон, VK или email — чтобы уточнить детали"
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                maxLength={200}
              />
            </label>
            {error && <p className="alert-error m-0">{error}</p>}
            <button
              type="submit"
              className="literary-btn literary-btn--primary w-full md:w-auto"
              disabled={loading || message.trim().length < 5}
            >
              {loading ? "Отправляю…" : "Отправить пожелание"}
            </button>
          </form>

          <aside className="space-y-4">
            <div className="page-panel page-panel--gold p-5">
              <h3 className="literary-title text-base m-0 mb-2">Примеры идей</h3>
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
            <p className="literary-page-note text-sm text-muted-foreground p-4 rounded-lg border border-border/60">
              Пожелания помогают развивать портал для жителей и гостей Пушкинских Гор — про дизайн, карту, объявления, жалобы и VK-бота.
            </p>
          </aside>
        </div>
      )}

      {!sent && (
        <p className="landing-section-verse text-center mt-10" aria-hidden>
          {LITERARY_VERSES.wishes}
        </p>
      )}
    </div>
  );
}
