import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import {
  ClassifiedAdForm,
  LiteraryEmptyState,
  LiteraryInlineLoader,
  LiteraryJobCard,
  LiterarySectionHead,
  PostSubmitPanel,
} from "@/components/literary";
import { VkBotBanner } from "@/components/VkBotLink";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api/index";
import type { ClassifiedAd } from "@/lib/api/types/classifieds";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { JOBS_DRAFT_KEY, JOBS_FORM_INITIAL, type ClassifiedAdFormState } from "@/lib/classifiedForm";
import { JOB_CATEGORY_IDS, JOB_FORM_HINTS, LOCAL_EMPLOYERS } from "@/lib/jobs";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useFormDraft } from "@/hooks/useFormDraft";

const copy = PAGE_SECTIONS.jobs;

export function Jobs() {
  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [sector, setSector] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [showForm, setShowForm] = useState(false);
  const { value: form, setValue: setForm, clearDraft } = useFormDraft<ClassifiedAdFormState>(JOBS_DRAFT_KEY, JOBS_FORM_INITIAL);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [submittedId, setSubmittedId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const successRef = useRef<HTMLDivElement | null>(null);

  const jobCategories = categories.filter((c) => JOB_CATEGORY_IDS.has(c.value));

  const load = (pageNum = 1, append = false) => {
    const params: Record<string, string> = {
      jobs_only: "true",
      page: String(pageNum),
      page_size: "20",
    };
    if (sector) params.category = sector;
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
    api.getClassifiedCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    load(1, false);
  }, [sector, search]);

  useEffect(() => {
    if (submittedId && successRef.current) {
      successRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [submittedId]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
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
      <PageHeader icon="💼" title={copy.title} subtitle={copy.lead}>
        <button type="button" className="literary-btn literary-btn--primary text-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "✕ Отмена" : "+ Разместить вакансию"}
        </button>
      </PageHeader>

      <div className="literary-page-note mb-6">
        <p className="m-0">
          Здесь — <strong>работа и подработка</strong> в посёлке и районе: музей-заповедник, гостиницы, магазины, ЖКХ.
          Дрова и услуги мастеров — в{" "}
          <Link to="/classifieds" className="literary-link">объявлениях</Link> и{" "}
          <Link to="/services" className="literary-link">справочнике услуг</Link>.
        </p>
      </div>

      <section className="page-panel page-panel--forest mb-6">
        <LiterarySectionHead
          kicker={copy.employers.kicker}
          title={copy.employers.title}
          lead={copy.employers.lead}
        />
        <div className="jobs-employers-grid">
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
      </section>

      <section className="page-panel page-panel--gold mb-4">
        <LiterarySectionHead
          kicker={copy.search.kicker}
          title={copy.search.title}
          lead={copy.search.lead}
        />
        <div className="flex flex-col sm:flex-row gap-2">
          <Input
            placeholder="Поиск: продавец, водитель, лето…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
            className="flex-1 pushkin-select"
          />
          <button type="button" className="literary-btn literary-btn--ghost shrink-0" onClick={() => setSearch(searchInput.trim())}>
            Найти
          </button>
        </div>
      </section>

      <div className="literary-filter-bar mb-6">
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

      {showForm && (
        <ClassifiedAdForm
          mode="jobs"
          categories={jobCategories}
          form={form}
          setForm={setForm}
          onSubmit={submit}
          submitting={submitting}
          showExtras
          onToggleExtras={() => undefined}
          hints={JOB_FORM_HINTS}
          kicker={copy.form.kicker}
          title={copy.form.title}
          lead={copy.form.lead}
          freeTitle="Бесплатная вакансия"
          freeLead="После модерации — на сайте и в VK-боте"
          agreeLabel="Вакансия настоящая, без предоплаты соискателям"
          submitLabel="Отправить на модерацию"
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
          hint={msgType === "ok" && submittedId ? "Обычно проверяем до суток. После публикации вакансия появится на доске." : undefined}
          actions={
            msgType === "ok" && submittedId ? (
              <button type="button" className="literary-link text-sm font-medium" onClick={() => setShowForm(true)}>
                Разместить ещё одну →
              </button>
            ) : undefined
          }
        />
      )}

      <div className="literary-jobs-list">
        {ads.map((ad) => (
          <LiteraryJobCard key={ad.id} ad={ad} />
        ))}
        {!loading && ads.length === 0 && (
          <LiteraryEmptyState {...EMPTY_STATES.jobs}>
            <button type="button" className="literary-btn literary-btn--primary mt-2" onClick={() => setShowForm(true)}>
              + Разместить вакансию
            </button>
          </LiteraryEmptyState>
        )}
        {loading && <LiteraryInlineLoader label="Ищем вакансии в округе…" />}
        {ads.length > 0 && ads.length < total && (
          <div className="text-center pt-4">
            <button type="button" className="literary-btn literary-btn--ghost" disabled={loading} onClick={() => load(page + 1, true)}>
              Ещё ({ads.length} из {total})
            </button>
          </div>
        )}
      </div>

      <div className="mt-8">
        <VkBotBanner />
      </div>
    </div>
  );
}
