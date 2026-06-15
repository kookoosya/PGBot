import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { VkBotBanner } from "@/components/VkBotLink";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api, Issue } from "@/lib/api";
import { EMPTY_STATES, LITERARY_VERSES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useUserAuth } from "@/lib/userAuth";
import { formatDate, issueStatusHint, STATUS_COLORS, STATUS_LABELS } from "@/lib/utils";

const copy = PAGE_SECTIONS.complaints;

export function Complaints() {
  const { user } = useUserAuth();
  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get("issue");
  const highlightRef = useRef<HTMLDivElement | null>(null);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [myIssues, setMyIssues] = useState<Issue[]>([]);
  const [showForm, setShowForm] = useState(true);
  const [showExtras, setShowExtras] = useState(false);
  const [form, setForm] = useState({
    description: "",
    address: "",
    category: "",
    full_name: "",
    phone: "",
    website_url: "",
  });
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    if (!user) {
      setMyIssues([]);
      return;
    }
    api.getMyIssues({ limit: "10" })
      .then((r) => setMyIssues(r.items))
      .catch(() => setMyIssues([]));
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
      setMsg(`Обращение #${issue.id} принято! Статус: на рассмотрении.`);
      setForm((f) => ({ ...f, description: "", address: "" }));
      if (user) {
        const r = await api.getMyIssues({ limit: "10" });
        setMyIssues(r.items);
      }
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Ошибка отправки");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="literary-page page-section max-w-5xl">
      <PageHeader icon="⚠️" title={copy.title} subtitle={copy.lead} />

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
            <form onSubmit={submit} className="page-panel page-panel--forest space-y-4 form-glow literary-form-comfort">
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
                <textarea
                  className="literary-textarea w-full min-h-[140px]"
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  placeholder="Например: не работает уличное освещение на перекрёстке..."
                  required
                  minLength={5}
                />
                <p className="text-sm text-muted-foreground mt-1 m-0">Достаточно пары предложений — категорию подскажет ИИ.</p>
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
                        <option key={c.value} value={c.label}>{c.label}</option>
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

              {msg && (
                <p className={msgType === "ok" ? "alert-success" : "alert-error"}>{msg}</p>
              )}

              <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={loading}>
                {loading ? "Отправляем…" : "Отправить обращение"}
              </button>

              {!user && (
                <p className="landing-muted text-xs text-center m-0">
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
            <section>
              <LiterarySectionHead
                kicker={copy.mine.kicker}
                title={copy.mine.title}
                lead={copy.mine.lead}
              />
              {myIssues.length === 0 ? (
                <LiteraryEmptyState {...EMPTY_STATES.complaintsMine} compact />
              ) : (
                <div className="space-y-3">
                  {myIssues.map((issue) => (
                    <article
                      key={issue.id}
                      ref={highlightId === String(issue.id) ? highlightRef : undefined}
                      className={`literary-issue-card literary-issue-card--static${highlightId === String(issue.id) ? " literary-issue-card--highlight" : ""}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="literary-issue-id">#{issue.id}</span>
                            <Badge className={STATUS_COLORS[issue.status]}>
                              {STATUS_LABELS[issue.status]}
                            </Badge>
                            {issue.category && (
                              <Badge className="bg-gray-100 text-gray-700">{issue.category}</Badge>
                            )}
                          </div>
                          <p className="literary-issue-summary mt-2">
                            {issue.ai_analysis?.summary || issue.description}
                          </p>
                          {issueStatusHint(issue.status) && (
                            <p className="text-sm text-muted-foreground mt-1">{issueStatusHint(issue.status)}</p>
                          )}
                          {issue.address && (
                            <p className="literary-issue-address">📍 {issue.address}</p>
                          )}
                        </div>
                        <span className="literary-issue-date">{formatDate(issue.created_at)}</span>
                      </div>

                      {issue.status_timeline && issue.status_timeline.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-dashed border-border/60">
                          <p className="event-detail-label mb-2">История статусов</p>
                          <ol className="issue-status-timeline">
                            {issue.status_timeline.map((event, index) => (
                              <li
                                key={`${event.at}-${event.status}-${index}`}
                                className={index === issue.status_timeline!.length - 1 ? "issue-status-timeline-item--current" : ""}
                              >
                                <span className="issue-status-timeline-dot" aria-hidden />
                                <div>
                                  <p className="issue-status-timeline-label">{event.label}</p>
                                  {event.previous_status && index > 0 && (
                                    <p className="issue-status-timeline-prev">
                                      из «{STATUS_LABELS[event.previous_status] || event.previous_status}»
                                    </p>
                                  )}
                                  {event.resolution && (
                                    <p className="issue-status-timeline-resolution">{event.resolution}</p>
                                  )}
                                  <p className="issue-status-timeline-date">{formatDate(event.at)}</p>
                                </div>
                              </li>
                            ))}
                          </ol>
                        </div>
                      )}

                      {issue.resolution_text && (
                        <div className="literary-page-note mt-3">
                          <strong>Ответ службы:</strong>
                          <p className="m-0 mt-1">{issue.resolution_text}</p>
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </section>
          )}

          <VkBotBanner />
        </div>
      </div>

      <p className="literary-page-verse" aria-hidden>{LITERARY_VERSES.complaints}</p>
    </div>
  );
}
