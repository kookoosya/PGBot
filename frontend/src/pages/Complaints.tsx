import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState, LiteraryIssueCard, LiterarySectionHead, PostSubmitPanel } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api/index";
import type { Issue } from "@/lib/api/types/issues";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useUserAuth } from "@/lib/userAuth";
import { ISSUE_ACTIVE_STATUSES, ISSUE_DONE_STATUSES } from "@/lib/utils";
import { useFormDraft } from "@/hooks/useFormDraft";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";

const ISSUE_FILTER_ACTIVE = ISSUE_ACTIVE_STATUSES;
const ISSUE_FILTER_DONE = ISSUE_DONE_STATUSES;
const COMPLAINT_TEMPLATES = [
  "Не работает уличное освещение возле дома.",
  "На дороге ямы, сложно проехать после дождя.",
  "Переполнены контейнеры, нужен вывоз мусора.",
];

type IssueFilter = "all" | "active" | "done";

const copy = PAGE_SECTIONS.complaints;
const COMPLAINTS_DRAFT_KEY = "complaints_form_draft_v1";

const FLOW_STEPS = [
  { icon: "✍️", title: "Опишите", text: "Достаточно пары предложений — адрес по желанию." },
  { icon: "🤖", title: "Передадим", text: "ИИ подскажет категорию, заявка уйдёт в службу." },
  { icon: "📬", title: "Следите", text: "Статус — в кабинете или во ВК-боте «Мои обращения»." },
];

export function Complaints() {
  useDocumentTitle(copy.title);
  const { user } = useUserAuth();
  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get("issue");
  const openNew = searchParams.get("new") === "1";
  const highlightRef = useRef<HTMLDivElement | null>(null);
  const issuesSectionRef = useRef<HTMLElement | null>(null);
  const formRef = useRef<HTMLFormElement | null>(null);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [myIssues, setMyIssues] = useState<Issue[]>([]);
  const [showForm, setShowForm] = useState(true);
  const [showExtras, setShowExtras] = useState(false);
  const initialForm = {
    description: "",
    address: "",
    category: "",
    full_name: "",
    phone: "",
    website_url: "",
  };
  const { value: form, setValue: setForm, clearDraft } = useFormDraft(COMPLAINTS_DRAFT_KEY, initialForm);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [loading, setLoading] = useState(false);
  const [submittedId, setSubmittedId] = useState<number | null>(null);
  const [categoriesError, setCategoriesError] = useState(false);
  const [issueFilter, setIssueFilter] = useState<IssueFilter>("all");
  const [issuesError, setIssuesError] = useState(false);

  useEffect(() => {
    api.getCategories()
      .then(setCategories)
      .catch(() => setCategoriesError(true));
  }, []);

  useEffect(() => {
    if (openNew) setShowForm(true);
  }, [openNew]);

  useEffect(() => {
    if (!user) {
      setMyIssues([]);
      setIssuesError(false);
      return;
    }
    setIssuesError(false);
    api.getMyIssues({ limit: "10" })
      .then((r) => setMyIssues(r.items))
      .catch(() => {
        setMyIssues([]);
        setIssuesError(true);
      });
  }, [user]);

  useEffect(() => {
    if (!highlightId || myIssues.length === 0) return;
    const el = highlightRef.current;
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlightId, myIssues]);

  useEffect(() => {
    if (user) {
      setForm((f) => ({
        ...f,
        full_name: user.full_name || f.full_name,
        phone: user.phone || f.phone,
      }));
    }
  }, [user]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formRef.current?.checkValidity()) {
      const firstInvalid = formRef.current?.querySelector<HTMLElement>(":invalid");
      firstInvalid?.focus();
      formRef.current?.reportValidity();
      return;
    }
    setLoading(true);
    setMsg("");
    try {
      const issue = await api.createIssue({
        description: form.description,
        address: form.address || undefined,
        category: form.category || undefined,
        full_name: user ? undefined : form.full_name,
        phone: user ? undefined : form.phone,
        website_url: form.website_url || undefined,
      });
      setMsgType("ok");
      setSubmittedId(issue.id);
      setMsg("Статус: на рассмотрении. Мы передадим обращение в службу.");
      setForm((f) => ({ ...f, description: "", address: "" }));
      clearDraft();
      if (user) {
        const r = await api.getMyIssues({ limit: "10" });
        setMyIssues(r.items);
        setTimeout(() => issuesSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 200);
      }
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Ошибка отправки");
    } finally {
      setLoading(false);
    }
  };

  const filteredIssues = myIssues.filter((issue) => {
    if (issueFilter === "active") return ISSUE_FILTER_ACTIVE.has(issue.status);
    if (issueFilter === "done") return ISSUE_FILTER_DONE.has(issue.status);
    return true;
  });

  return (
    <div className="literary-page page-section max-w-5xl">
      <PageHeader icon="⚠️" title={copy.title} subtitle={copy.lead}>
        {!user && (
          <Link to="/cabinet/login?next=/complaints" className="literary-btn literary-btn--ghost text-sm no-underline">
            Войти для истории
          </Link>
        )}
      </PageHeader>

      <section className="page-panel page-panel--gold mb-6" aria-label="Как подать обращение">
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

      {user && myIssues.length > 0 && (
        <div className="page-section pb-2">
          <div className="map-stats-ribbon" aria-label="Мои обращения">
            <div className="map-stats-ribbon-head">
              <p className="map-stats-ribbon-total m-0">
                <strong>{myIssues.length}</strong>{" "}
                {myIssues.length === 1 ? "обращение" : myIssues.length < 5 ? "обращения" : "обращений"}
              </p>
              <p className="map-stats-ribbon-sync m-0">
                В работе: {myIssues.filter((i) => ISSUE_FILTER_ACTIVE.has(i.status)).length}
                {" · "}
                Завершено: {myIssues.filter((i) => ISSUE_FILTER_DONE.has(i.status)).length}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-2">
        <div>
          <div className="flex items-center justify-between mb-4">
            <LiterarySectionHead
              kicker={copy.form.kicker}
              title={copy.form.title}
              lead={copy.form.lead}
            />
            <button type="button" className="literary-btn literary-btn--ghost text-sm shrink-0" onClick={() => setShowForm(!showForm)}>
              {showForm ? "Свернуть" : "Открыть форму"}
            </button>
          </div>

          {showForm && (
            <form ref={formRef} onSubmit={submit} className="page-panel page-panel--forest space-y-4 form-glow literary-form-comfort">
              {!user && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="event-detail-label">Ваше имя</label>
                    <Input
                      value={form.full_name}
                      onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                      required
                    />
                  </div>
                  <div>
                    <label className="event-detail-label">Телефон</label>
                    <Input
                      value={form.phone}
                      onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                      placeholder="+7..."
                      required
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="event-detail-label">Что случилось?</label>
                <div className="suggest-chips mb-2">
                  {COMPLAINT_TEMPLATES.map((template) => (
                    <button
                      key={template}
                      type="button"
                      className="suggest-chip"
                      onClick={() => setForm((f) => ({ ...f, description: template }))}
                    >
                      {template}
                    </button>
                  ))}
                </div>
                <textarea
                  className="literary-textarea w-full min-h-[140px]"
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  placeholder="Например: не работает уличное освещение на перекрёстке..."
                  required
                  minLength={5}
                />
                <p className="text-sm text-muted-foreground mt-1 m-0">
                  Достаточно пары предложений — категорию подскажет ИИ.
                  <span className={`form-char-count${form.description.trim().length < 5 ? " form-char-count--warn" : ""}`}>
                    {" "}
                    {form.description.trim().length} симв. (мин. 5)
                  </span>
                </p>
              </div>

              <button
                type="button"
                className="literary-btn literary-btn--ghost text-sm w-full"
                onClick={() => setShowExtras(!showExtras)}
              >
                {showExtras ? "Скрыть дополнительно" : "Адрес и категория (необязательно)"}
              </button>

              {showExtras && (
                <>
                  <div>
                    <label className="event-detail-label">Категория</label>
                    <select
                      className="pushkin-select w-full"
                      value={form.category}
                      onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                    >
                      <option value="">Авто (ИИ определит)</option>
                      {categories.map((c) => (
                        <option key={c.value} value={c.value}>{c.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="event-detail-label">Адрес / место</label>
                    <Input
                      value={form.address}
                      onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                      placeholder="ул. Ленина, 5"
                    />
                  </div>
                </>
              )}

              <input
                type="text"
                name="website_url"
                value={form.website_url}
                onChange={(e) => setForm((f) => ({ ...f, website_url: e.target.value }))}
                className="honeypot-field"
                tabIndex={-1}
                autoComplete="off"
                aria-hidden="true"
              />

              {categoriesError && (
                <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 m-0">
                  Список категорий временно недоступен — ИИ определит её автоматически.
                </p>
              )}

              {msg && (
                <PostSubmitPanel
                  tone={msgType}
                  message={msg}
                  entityId={submittedId}
                  entityNoun="Обращение"
                  hint={
                    msgType === "ok" && submittedId
                      ? "Статус появится в списке справа. Уведомление придёт и в VK-бот — напишите «Мои обращения»."
                      : undefined
                  }
                  actions={
                    msgType === "ok" && submittedId ? (
                      user ? (
                        <Link to={`/complaints?issue=${submittedId}`} className="literary-link text-sm font-medium">
                          Посмотреть статус обращения →
                        </Link>
                      ) : (
                        <Link
                          to={`/cabinet/login?next=/complaints?issue=${submittedId}`}
                          className="literary-link text-sm font-medium"
                        >
                          Войти, чтобы отслеживать статус →
                        </Link>
                      )
                    ) : undefined
                  }
                />
              )}

              <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={loading}>
                {loading ? "Отправляем…" : "Отправить обращение"}
              </button>
              <p className="text-sm text-muted-foreground text-center m-0">Черновик сохраняется автоматически.</p>
              {!loading && (
                <button
                  type="button"
                  className="literary-btn literary-btn--ghost w-full text-sm"
                  onClick={() =>
                    setForm((f) => ({
                      ...f,
                      description: "",
                      address: "",
                      category: "",
                    }))
                  }
                >
                  Очистить форму
                </button>
              )}

              {!user && (
                <p className="landing-muted text-sm text-center m-0">
                  <Link to="/cabinet/login" className="literary-link">Войдите</Link>
                  {" "}чтобы видеть историю обращений
                </p>
              )}
            </form>
          )}
        </div>

        <div className="space-y-6">
          <section className="page-panel page-panel--gold">
            <LiterarySectionHead
              kicker={copy.orgs.kicker}
              title={copy.orgs.title}
              lead={copy.orgs.lead}
            />
            <div className="flex flex-wrap gap-2">
              <Link to="/register" className="literary-btn literary-btn--primary text-sm no-underline">Регистрация</Link>
              <Link to="/cabinet/login?next=/official" className="literary-btn literary-btn--ghost text-sm no-underline">Вход для служб</Link>
            </div>
          </section>

          {highlightId && !user && (
            <section className="page-panel page-panel--gold mb-4">
              <p className="m-0 text-sm">
                Чтобы увидеть обращение #{highlightId},{" "}
                <Link to={`/cabinet/login?next=/complaints?issue=${highlightId}`} className="literary-link">
                  войдите в кабинет
                </Link>
                {" "}или напишите боту «Мои обращения».
              </p>
            </section>
          )}

          {user && (
            <section ref={issuesSectionRef}>
              <LiterarySectionHead
                kicker={copy.mine.kicker}
                title={copy.mine.title}
                lead={copy.mine.lead}
              />
              {myIssues.length > 0 && (
                <div className="literary-filter-bar mb-4">
                  <button
                    type="button"
                    className={`filter-chip${issueFilter === "all" ? " filter-chip-active" : ""}`}
                    onClick={() => setIssueFilter("all")}
                  >
                    Все ({myIssues.length})
                  </button>
                  <button
                    type="button"
                    className={`filter-chip${issueFilter === "active" ? " filter-chip-active" : ""}`}
                    onClick={() => setIssueFilter("active")}
                  >
                    В работе ({myIssues.filter((i) => ISSUE_FILTER_ACTIVE.has(i.status)).length})
                  </button>
                  <button
                    type="button"
                    className={`filter-chip${issueFilter === "done" ? " filter-chip-active" : ""}`}
                    onClick={() => setIssueFilter("done")}
                  >
                    Завершённые ({myIssues.filter((i) => ISSUE_FILTER_DONE.has(i.status)).length})
                  </button>
                </div>
              )}
              {issuesError ? (
                <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                  Не удалось загрузить обращения. Обновите страницу чуть позже.
                </p>
              ) : myIssues.length === 0 ? (
                <LiteraryEmptyState {...EMPTY_STATES.complaintsMine} compact />
              ) : filteredIssues.length === 0 ? (
                <p className="text-sm text-muted-foreground">По этому фильтру обращений нет.</p>
              ) : (
                <div className="space-y-3">
                  {filteredIssues.map((issue) => (
                    <LiteraryIssueCard
                      key={issue.id}
                      issue={issue}
                      variant="static"
                      highlighted={highlightId === String(issue.id)}
                      cardRef={highlightId === String(issue.id) ? highlightRef : undefined}
                      showStatusHint
                      showTimeline
                      showResolution
                    />
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
