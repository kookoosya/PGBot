import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import {
  ClassifiedAdForm,
  LiteraryEmptyState,
  LiteraryInlineLoader,
  LiteraryJobCard,
  LiterarySectionHead,
  PostSubmitPanel,
} from "@/components/literary";
import { Input } from "@/components/ui/input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { api } from "@/lib/api/index";
import type { ClassifiedAd } from "@/lib/api/types/classifieds";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { JOBS_DRAFT_KEY, JOBS_FORM_INITIAL, type ClassifiedAdFormState } from "@/lib/classifiedForm";
import { JOB_CATEGORY_IDS, JOB_FORM_HINTS, LOCAL_EMPLOYERS } from "@/lib/jobs";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useFormDraft } from "@/hooks/useFormDraft";

const copy = PAGE_SECTIONS.jobs;

const FLOW_STEPS = [
  { icon: "✍️", title: "Разместите", text: "Бесплатно — вакансия или подработка в посёлке." },
  { icon: "✅", title: "Проверка", text: "Текст проходит автоматическую модерацию." },
  { icon: "📞", title: "Отклик", text: "Соседи звонят напрямую — без посредников." },
];

export function Jobs() {
  const [searchParams] = useSearchParams();
  const openNew = searchParams.get("new") === "1";

  useDocumentTitle(copy.title);

  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [sector, setSector] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [showForm, setShowForm] = useState(openNew);
  const { value: form, setValue: setForm, clearDraft } = useFormDraft<ClassifiedAdFormState>(JOBS_DRAFT_KEY, JOBS_FORM_INITIAL);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [submittedId, setSubmittedId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const successRef = useRef<HTMLDivElement | null>(null);
  const formRef = useRef<HTMLFormElement | null>(null);

  const jobCategories = categories.filter((c) => JOB_CATEGORY_IDS.has(c.value));
  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  useEffect(() => {
    const t = window.setTimeout(() => setSearch(searchInput.trim()), 400);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    if (openNew) setShowForm(true);
  }, [openNew]);

  useEffect(() => {
    api.getClassifiedCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    const params: Record<string, string> = {
      jobs_only: "true",
      page: "1",
      page_size: "20",
    };
    if (sector) params.category = sector;
    if (search) params.search = search;
    setLoading(true);
    setLoadError(false);
    api
      .getClassifieds(params)
      .then((r) => {
        setTotal(r.total);
        setPage(1);
        setAds(r.items);
      })
      .catch(() => {
        setAds([]);
        setTotal(0);
        setLoadError(true);
      })
      .finally(() => setLoading(false));
  }, [sector, search, reloadToken]);

  useEffect(() => {
    if (submittedId && successRef.current) {
      successRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [submittedId]);

  const loadMore = () => {
    const params: Record<string, string> = {
      jobs_only: "true",
      page: String(page + 1),
      page_size: "20",
    };
    if (sector) params.category = sector;
    if (search) params.search = search;
    setLoading(true);
    api
      .getClassifieds(params)
      .then((r) => {
        setTotal(r.total);
        setPage((p) => p + 1);
        setAds((prev) => [...prev, ...r.items]);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formRef.current?.checkValidity()) {
      const firstInvalid = formRef.current?.querySelector<HTMLElement>(":invalid");
      firstInvalid?.focus();
      formRef.current?.reportValidity();
      return;
    }
    setSubmitting(true);
    setMsg("");
    try {
      const res = await api.createClassified({ ...form, price: form.price ? +form.price : undefined });
      setMsgType("ok");
      setSubmittedId(res.id);
      setMsg(res.message);
      setShowForm(false);
      setForm((f) => ({
        ...f,
        title: "",
        description: "",
        price: "",
        contact_vk: "",
        website_url: "",
        agree_rules: false,
      }));
      clearDraft();
      reload();
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setSubmitting(false);
    }
  };

  const emptyState = search || sector ? EMPTY_STATES.jobsSearch : EMPTY_STATES.jobs;

  return (
    <div className="literary-page page-section max-w-5xl">
      <PageHeader icon="💼" title={copy.title} subtitle={copy.lead}>
        <button type="button" className="literary-btn literary-btn--primary text-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "✕ Отмена" : "+ Разместить вакансию"}
        </button>
      </PageHeader>

      <section className="page-panel page-panel--gold mb-6" aria-label="Как разместить вакансию">
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

      {!loadError && total > 0 && (
        <div className="page-section pb-2">
          <div className="map-stats-ribbon" aria-label="Статистика вакансий">
            <div className="map-stats-ribbon-head">
              <p className="map-stats-ribbon-total m-0">
                <strong>{total}</strong> {sector || search ? "вакансий в выборке" : "вакансий на доске"}
              </p>
              <p className="map-stats-ribbon-sync m-0">Бесплатно — публикуем сразу после проверки текста</p>
            </div>
          </div>
        </div>
      )}

      <section className="page-panel page-panel--forest mb-6">
        <LiterarySectionHead kicker={copy.search.kicker} title={copy.search.title} lead={copy.search.lead} compact />
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <Input
            placeholder={copy.search.placeholder}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
            className="flex-1 pushkin-select"
          />
          {search && (
            <button
              type="button"
              className="literary-btn literary-btn--ghost shrink-0 text-sm"
              onClick={() => {
                setSearch("");
                setSearchInput("");
              }}
            >
              Сбросить
            </button>
          )}
          <button type="button" className="literary-btn literary-btn--ghost shrink-0" onClick={() => setSearch(searchInput.trim())}>
            Найти
          </button>
        </div>
        <div className="literary-filter-bar">
          <button
            type="button"
            className={`filter-chip${!sector ? " filter-chip-active" : ""}`}
            onClick={() => setSector("")}
          >
            🪶 Все {total > 0 && `(${total})`}
          </button>
          {jobCategories.map((c) => {
            const visual = getCategoryVisual(c.value);
            return (
              <button
                key={c.value}
                type="button"
                className={`filter-chip${sector === c.value ? " filter-chip-active" : ""}`}
                onClick={() => setSector(c.value)}
              >
                {visual.icon} {c.label}
              </button>
            );
          })}
        </div>
      </section>

      {showForm && (
        <ClassifiedAdForm
          mode="jobs"
          categories={jobCategories}
          form={form}
          setForm={setForm}
          onSubmit={submit}
          formRef={formRef}
          submitting={submitting}
          showExtras
          onToggleExtras={() => undefined}
          hints={JOB_FORM_HINTS}
          kicker={copy.form.kicker}
          title={copy.form.title}
          lead={copy.form.lead}
          freeTitle={copy.form.freeTitle}
          freeLead={copy.form.freeLead}
          agreeLabel={copy.form.agreeLabel}
          submitLabel={copy.form.submitLabel}
          showDraftNote
        />
      )}

      {msg && (
        <PostSubmitPanel
          panelRef={successRef}
          tone={msgType}
          message={msg}
          entityId={submittedId}
          entityNoun="Вакансия"
          variant="gold-panel"
          hint={msgType === "ok" && submittedId ? "Вакансия уже на доске — соседи могут откликнуться." : undefined}
          actions={
            msgType === "ok" && submittedId ? (
              <>
                <Link to="/jobs" className="literary-link text-sm font-medium">
                  Вернуться к доске →
                </Link>
                <button type="button" className="literary-link text-sm font-medium" onClick={() => setShowForm(true)}>
                  Разместить ещё одну →
                </button>
              </>
            ) : undefined
          }
        />
      )}

      {loadError && !loading && (
        <LiteraryEmptyState icon="⚠️" title="Доска временно недоступна" text="Не удалось загрузить вакансии. Попробуйте ещё раз.">
          <button type="button" className="literary-btn literary-btn--primary mt-3" onClick={reload}>
            Повторить
          </button>
        </LiteraryEmptyState>
      )}

      {!loadError && (
        <section className="mb-6">
          <LiterarySectionHead kicker="💼 Доска" title="Вакансии" lead="Работа в посёлке и районе — звоните напрямую работодателю." compact />
          <div className="literary-jobs-list">
            {ads.map((ad) => (
              <LiteraryJobCard key={ad.id} ad={ad} />
            ))}
            {!loading && ads.length === 0 && (
              <LiteraryEmptyState {...emptyState}>
                <button type="button" className="literary-btn literary-btn--primary mt-2" onClick={() => setShowForm(true)}>
                  + Разместить вакансию
                </button>
              </LiteraryEmptyState>
            )}
            {loading && <LiteraryInlineLoader label="Ищем вакансии…" />}
            {ads.length > 0 && ads.length < total && (
              <div className="text-center pt-4">
                <button type="button" className="literary-btn literary-btn--ghost" disabled={loading} onClick={loadMore}>
                  Ещё ({ads.length} из {total})
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      <details className="jobs-employers-details page-panel page-panel--gold">
        <summary className="jobs-employers-summary">
          <span>{copy.employers.title}</span>
          <span className="jobs-employers-summary-hint">{copy.employers.lead}</span>
        </summary>
        <div className="jobs-employers-grid mt-4">
          {LOCAL_EMPLOYERS.map((e) => (
            <div key={e.title} className="jobs-employer-card jobs-employer-card--literary">
              <span className="jobs-employer-icon">{e.icon}</span>
              <div>
                <h3 className="jobs-employer-title">{e.title}</h3>
                <p className="jobs-employer-desc">{e.desc}</p>
              </div>
            </div>
          ))}
        </div>
        <p className="landing-muted text-sm mt-4 mb-0">
          Подработка и услуги — в{" "}
          <Link to="/classifieds/services" className="literary-link">
            объявлениях
          </Link>{" "}
          и{" "}
          <Link to="/services" className="literary-link">
            справочнике услуг
          </Link>
          .
        </p>
      </details>
    </div>
  );
}
