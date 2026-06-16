import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import {
  ClassifiedAdForm,
  LiteraryClassifiedCard,
  LiteraryEmptyState,
  LiteraryInlineLoader,
  LiterarySectionHead,
  PostSubmitPanel,
} from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { CLASSIFIED_FORM_INITIAL, CLASSIFIEDS_DRAFT_KEY, type ClassifiedAdFormState } from "@/lib/classifiedForm";
import { JOB_CATEGORY_IDS } from "@/lib/jobs";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useFormDraft } from "@/hooks/useFormDraft";

export function Classifieds() {
  const [searchParams] = useSearchParams();
  const neighborMode = searchParams.get("neighbor") === "1";
  const openNew = searchParams.get("new") === "1";
  if (searchParams.get("jobs") === "1") {
    return <Navigate to="/jobs" replace />;
  }

  const pageCopy = neighborMode ? PAGE_SECTIONS.classifieds.neighbor : PAGE_SECTIONS.classifieds;

  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [filter, setFilter] = useState("");
  const [showForm, setShowForm] = useState(openNew);
  const [showExtras, setShowExtras] = useState(false);
  const initialForm = CLASSIFIED_FORM_INITIAL;
  const { value: form, setValue: setForm, clearDraft } = useFormDraft<ClassifiedAdFormState>(CLASSIFIEDS_DRAFT_KEY, initialForm);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [submittedId, setSubmittedId] = useState<number | null>(null);
  const [submittedNotifyVk, setSubmittedNotifyVk] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const successRef = useRef<HTMLDivElement | null>(null);
  const formRef = useRef<HTMLFormElement | null>(null);

  const adCategories = categories.filter((c) => !JOB_CATEGORY_IDS.has(c.value));

  const load = (pageNum = 1, append = false) => {
    const params: Record<string, string> = {
      page: String(pageNum),
      page_size: "20",
    };
    if (neighborMode) {
      params.neighbor_only = "true";
    } else {
      params.ads_only = "true";
    }
    if (filter) params.category = filter;
    if (search) params.search = search;
    setLoading(true);
    api
      .getClassifieds(params)
      .then((r) => {
        setTotal(r.total);
        setPage(pageNum);
        setAds(append ? (prev) => [...prev, ...r.items] : r.items);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (openNew) setShowForm(true);
  }, [openNew]);

  useEffect(() => {
    if (submittedId && successRef.current) {
      successRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [submittedId]);

  useEffect(() => {
    api.getClassifiedCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    load(1, false);
  }, [filter, search, neighborMode]);

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
      const res = await api.createClassified({
        ...form,
        price: form.price ? +form.price : undefined,
      });
      setMsgType("ok");
      setSubmittedId(res.id);
      setSubmittedNotifyVk(!!form.contact_vk.trim());
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
      load(1, false);
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="literary-page page-section max-w-5xl">
      <PageHeader
        icon={neighborMode ? "🤝" : "📋"}
        title={neighborMode ? pageCopy.title : PAGE_SECTIONS.classifieds.title}
        subtitle={pageCopy.lead}
      >
        <button type="button" className="literary-btn literary-btn--primary text-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "✕ Отмена" : "+ Подать объявление"}
        </button>
      </PageHeader>

      <div className="literary-page-note mb-6">
        <p className="m-0">
          Дрова, покос, продажа, аренда — <strong>бесплатно и без регистрации</strong>.
          Вакансии — на{" "}
          <Link to="/jobs" className="literary-link">«Работа»</Link>,
          мастера — в{" "}
          <Link to="/services" className="literary-link">«Услуги»</Link>,
          взаимная помощь —{" "}
          <Link to="/classifieds?neighbor=1" className="literary-link">«Сосед помогает»</Link>.
        </p>
      </div>

      <section className="page-panel page-panel--gold mb-4">
        <LiterarySectionHead
          kicker="🔍 Поиск"
          title="Найти объявление"
          compact
        />
        <div className="space-y-2">
          <label htmlFor="classified-search-input" className="event-detail-label">Поиск по объявлениям</label>
          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              id="classified-search-input"
              placeholder="Поиск по заголовку…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
              className="flex-1 pushkin-select"
            />
            {search && (
              <button
                type="button"
                className="literary-btn literary-btn--ghost shrink-0 text-sm"
                onClick={() => { setSearch(""); setSearchInput(""); }}
              >
                Сбросить
              </button>
            )}
            <button type="button" className="literary-btn literary-btn--ghost shrink-0" onClick={() => setSearch(searchInput.trim())}>
              Найти
            </button>
          </div>
        </div>
      </section>

      <div className="literary-filter-bar mb-6">
        <button
          type="button"
          className={`filter-chip${!filter ? " filter-chip-active" : ""}`}
          onClick={() => setFilter("")}
        >
          🪶 Все {total > 0 && `(${total})`}
        </button>
        {adCategories.map((c) => {
          const visual = getCategoryVisual(c.value);
          return (
            <button
              key={c.value}
              type="button"
              className={`filter-chip${filter === c.value ? " filter-chip-active" : ""}`}
              onClick={() => setFilter(c.value)}
            >
              {visual.icon} {c.label}
            </button>
          );
        })}
      </div>

      {showForm && (
        <ClassifiedAdForm
          mode="classifieds"
          categories={adCategories}
          form={form}
          setForm={setForm}
          onSubmit={submit}
          formRef={formRef}
          submitting={submitting}
          showExtras={showExtras}
          onToggleExtras={() => setShowExtras(!showExtras)}
          kicker="✍️ Новое объявление"
          title="Подать на модерацию"
          freeTitle="Бесплатное размещение"
          freeLead="Честные объявления — без предоплаты и переводов незнакомцам."
          agreeLabel="Объявление честное: без предоплаты и переводов незнакомцам."
          submitLabel="🆓 Отправить на модерацию"
          showDraftNote
        />
      )}

      {msg && (
        <PostSubmitPanel
          panelRef={successRef}
          tone={msgType}
          message={msg}
          entityId={submittedId}
          entityNoun="Объявление"
          variant="gold-panel"
          hint={
            msgType === "ok" && submittedId
              ? `Обычно проверяем до суток. После публикации объявление появится на доске.${
                  submittedNotifyVk ? " Уведомим в VK." : " Укажите ВК в форме — пришлём сообщение, когда опубликуем."
                }`
              : undefined
          }
          actions={
            msgType === "ok" && submittedId ? (
              <>
                <Link to="/classifieds" className="literary-link text-sm font-medium">
                  Вернуться к доске →
                </Link>
                <button type="button" className="literary-link text-sm font-medium" onClick={() => setShowForm(true)}>
                  Подать ещё одно →
                </button>
              </>
            ) : undefined
          }
        />
      )}

      <div className="literary-classified-list">
        {ads.map((ad) => (
          <LiteraryClassifiedCard key={ad.id} ad={ad} compact />
        ))}
        {!loading && ads.length === 0 && (
          <LiteraryEmptyState {...EMPTY_STATES.classifieds}>
            <button type="button" className="literary-btn literary-btn--primary mt-2" onClick={() => setShowForm(true)}>
              + Подать объявление
            </button>
          </LiteraryEmptyState>
        )}
        {loading && <LiteraryInlineLoader label="Ищем объявления соседей…" />}
        {ads.length > 0 && ads.length < total && (
          <div className="text-center pt-4">
            <button type="button" className="literary-btn literary-btn--ghost" disabled={loading} onClick={() => load(page + 1, true)}>
              Ещё объявления ({ads.length} из {total})
            </button>
          </div>
        )}
      </div>

    </div>
  );
}
