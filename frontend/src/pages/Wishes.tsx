import { FormEvent, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { useFormDraft } from "@/hooks/useFormDraft";
import { api } from "@/lib/api/index";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useUserAuth } from "@/lib/userAuth";

const copy = PAGE_SECTIONS.wishes;
const WISHES_DRAFT_KEY = "wishes_form_draft_v1";

const FLOW_STEPS = [
  { icon: "💡", title: "Идея", text: "Что улучшить на сайте — раздел, карта, бот, дизайн." },
  { icon: "📨", title: "Отправка", text: "Пожелание попадёт администратору портала." },
  { icon: "🌱", title: "Развитие", text: "Лучшие идеи учитываем при обновлениях." },
];

const IDEA_CHIPS = [
  "Расписание автобусов",
  "Уведомления о новых объявлениях",
  "Фотоотчёты по обращениям",
  "Календарь мероприятий посёлка",
  "Раздел для туристов",
];

export function Wishes() {
  useDocumentTitle(copy.title);
  const { user } = useUserAuth();
  const location = useLocation();
  const initialForm = { message: "", contact: "" };
  const { value: form, setValue: setForm, clearDraft } = useFormDraft(WISHES_DRAFT_KEY, initialForm);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user && !form.contact) {
      setForm((f) => ({ ...f, contact: user.phone || user.email || "" }));
    }
  }, [user, form.contact, setForm]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.submitFeedback({
        message: form.message.trim(),
        contact: form.contact.trim() || undefined,
        page: location.pathname,
      });
      setSent(true);
      clearDraft();
      setForm(initialForm);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось отправить");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="literary-page page-section max-w-3xl">
      <PageHeader icon="💡" title={copy.title} subtitle={copy.lead} />

      <section className="page-panel page-panel--gold mb-6" aria-label="Как отправить пожелание">
        <div className="complaints-flow">
          {FLOW_STEPS.map((step) => (
            <div key={step.title} className="complaints-flow-step">
              <span className="complaints-flow-icon" aria-hidden>{step.icon}</span>
              <div>
                <p className="complaints-flow-title m-0">{step.title}</p>
                <p className="complaints-flow-text m-0">{step.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {sent ? (
        <LiteraryEmptyState {...EMPTY_STATES.wishesSent}>
          <button type="button" className="literary-btn literary-btn--ghost mt-3" onClick={() => setSent(false)}>
            Отправить ещё
          </button>
        </LiteraryEmptyState>
      ) : (
        <form onSubmit={submit} className="page-panel page-panel--forest space-y-4">
          <LiterarySectionHead kicker="✍️ Идея" title="Ваше пожелание" lead="Опишите, что улучшить — без лишних формальностей." compact />

          <div className="suggest-chips">
            {IDEA_CHIPS.map((idea) => (
              <button
                key={idea}
                type="button"
                className="suggest-chip"
                onClick={() => setForm((f) => ({ ...f, message: f.message ? `${f.message}\n${idea}` : idea }))}
              >
                {idea}
              </button>
            ))}
          </div>

          <label className="block text-sm font-semibold">
            Текст пожелания
            <textarea
              className="literary-textarea w-full min-h-[160px] mt-2"
              placeholder="Опишите, что улучшить на сайте, какой раздел добавить, что неудобно…"
              value={form.message}
              onChange={(e) => setForm((f) => ({ ...f, message: e.target.value }))}
              required
              minLength={5}
              maxLength={4000}
            />
          </label>
          <p className="text-sm text-muted-foreground m-0 -mt-2">
            <span className={form.message.trim().length < 5 ? "form-char-count form-char-count--warn" : "form-char-count"}>
              {form.message.trim().length} симв. (мин. 5)
            </span>
          </p>

          <label className="block text-sm font-semibold">
            Контакт (необязательно)
            <input
              className="pushkin-select w-full mt-2"
              placeholder="Телефон, VK или email — чтобы уточнить детали"
              value={form.contact}
              onChange={(e) => setForm((f) => ({ ...f, contact: e.target.value }))}
              maxLength={200}
            />
          </label>

          {error && <p className="alert-error m-0">{error}</p>}

          <button
            type="submit"
            className="literary-btn literary-btn--primary w-full"
            disabled={loading || form.message.trim().length < 5}
          >
            {loading ? "Отправляю…" : "Отправить пожелание"}
          </button>
          <p className="text-sm text-muted-foreground text-center m-0">Черновик сохраняется автоматически.</p>
        </form>
      )}
    </div>
  );
}
