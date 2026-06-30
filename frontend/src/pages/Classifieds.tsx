import { useCallback, useEffect, useRef, useState } from "react";
import { Link, Navigate, useLocation, useSearchParams } from "react-router-dom";
import { ClassifiedBoardTabs } from "@/components/classifieds/ClassifiedBoardTabs";
import { PageHeader } from "@/components/PageHeader";
import {
  ClassifiedAdForm,
  LiteraryClassifiedCard,
  LiteraryEmptyState,
  LiteraryInlineLoader,
  LiterarySectionHead,
  PostSubmitPanel,
} from "@/components/literary";
import { VkBotBanner } from "@/components/VkBotLink";
import { Input } from "@/components/ui/input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { api } from "@/lib/api/index";
import type { ClassifiedAd } from "@/lib/api/types/classifieds";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import {
  boardApiParams,
  boardFromPath,
  categoriesForBoard,
  CATEGORY_GROUPS,
  getBoard,
  type ClassifiedBoardId,
} from "@/lib/classifiedBoard";
import { CLASSIFIED_FORM_INITIAL, CLASSIFIEDS_DRAFT_KEY, type ClassifiedAdFormState } from "@/lib/classifiedForm";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useFormDraft } from "@/hooks/useFormDraft";

const formCopy = PAGE_SECTIONS.classifieds.form;
const searchCopy = PAGE_SECTIONS.classifieds.search;

export function Classifieds() {
  const { pathname } = useLocation();
  const [searchParams] = useSearchParams();
  const boardId: ClassifiedBoardId = boardFromPath(pathname);
  const board = getBoard(boardId);
  const openNew = searchParams.get("new") === "1";

  if (searchParams.get("jobs") === "1") {
    return <Navigate to="/jobs" replace />;
  }
  if (searchParams.get("neighbor") === "1") {
    return <Navigate to="/classifieds/help" replace />;
  }

  useDocumentTitle(board.title);

  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [filter, setFilter] = useState("");
  const [showForm, setShowForm] = useState(openNew);
  const [showExtras, setShowExtras] = useState(false);
  const { value: form, setValue: setForm, clearDraft } = useFormDraft<ClassifiedAdFormState>(
    CLASSIFIEDS_DRAFT_KEY,
    CLASSIFIED_FORM_INITIAL,
  );
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [submittedId, setSubmittedId] = useState<number | null>(null);
  const [submittedNotifyVk, setSubmittedNotifyVk] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const successRef = useRef<HTMLDivElement | null>(null);
  const formRef = useRef<HTMLFormElement | null>(null);

  const boardCategories = categoriesForBoard(boardId, categories);
  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  useEffect(() => {
    const t = window.setTimeout(() => setSearch(searchInput.trim()), 400);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    if (openNew) setShowForm(true);
  }, [openNew]);

  useEffect(() => {
    setFilter("");
  }, [boardId]);

  useEffect(() => {
    if (showForm && boardId === "help" && !form.category) {
      setForm((f) => ({ ...f, category: "neighbor_help" }));
    }
  }, [showForm, boardId, form.category, setForm]);

  useEffect(() => {
    if (submittedId && successRef.current) {
      successRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [submittedId]);

  useEffect(() => {
    api.getClassifiedCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    const params: Record<string, string> = {
      page: "1",
      page_size: "20",
      ...boardApiParams(boardId),
    };
    if (filter) params.category = filter;
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
  }, [filter, search, boardId, reloadToken]);

  const loadMore = () => {
    const params: Record<string, string> = {
      page: String(page + 1),
      page_size: "20",
      ...boardApiParams(boardId),
    };
    if (filter) params.category = filter;
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
      reload();
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setSubmitting(false);
    }
  };

  const emptyState =
    search || filter
      ? EMPTY_STATES.classifiedsSearch
      : boardId === "help"
        ? { ...EMPTY_STATES.classifieds, title: "Пока никто не просит помощи", text: board.lead }
        : EMPTY_STATES.classifieds;

  const renderCategoryChip = (c: { value: string; label: string }) => {
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
  };

  return (
    <div className="literary-page page-section max-w-5xl">
      <PageHeader icon={board.icon} title={board.title} subtitle={board.lead}>
        <button type="button" className="literary-btn literary-btn--primary text-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "✕ Отмена" : "+ Подать объявление"}
        </button>
      </PageHeader>

      <ClassifiedBoardTabs />

      {!loadError && total > 0 && (
        <div className="page-section pb-2">
          <div className="map-stats-ribbon" aria-label="Статистика доски">
            <div className="map-stats-ribbon-head">
              <p className="map-stats-ribbon-total m-0">
                <strong>{total}</strong> {board.ribbonLabel}
              </p>
              <p className="map-stats-ribbon-sync m-0">Публикуем сразу после проверки текста</p>
            </div>
          </div>
        </div>
      )}

      <div className="literary-page-note mb-6">
        <p className="m-0">
          {PAGE_SECTIONS.classifieds.note} Вакансии —{" "}
          <Link to="/jobs" className="literary-link">
            «Работа»
          </Link>
          , мастера с записью —{" "}
          <Link to="/services" className="literary-link">
            «Услуги»
          </Link>
          .
        </p>
      </div>

      <section className="page-panel page-panel--gold mb-4">
        <LiterarySectionHead kicker={searchCopy.kicker} title={searchCopy.title} compact />
        <div className="space-y-2">
          <label htmlFor="classified-search-input" className="event-detail-label">
            Поиск по объявлениям
          </label>
          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              id="classified-search-input"
              placeholder="Дрова, покос, продам, сдам…"
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
        </div>
      </section>

      {boardCategories.length > 0 && (
        <section className="page-panel page-panel--forest mb-6">
          <LiterarySectionHead kicker="🏷️ Категории" title="Уточнить раздел" compact />
          {boardId === "all" ? (
            <div className="classified-category-groups">
              {CATEGORY_GROUPS.map((group) => {
                const items = boardCategories.filter((c) => group.ids.has(c.value));
                if (items.length === 0) return null;
                return (
                  <div key={group.label} className="classified-category-group">
                    <p className="classified-category-group-label">{group.label}</p>
                    <div className="literary-filter-bar classified-category-group-chips">{items.map(renderCategoryChip)}</div>
                  </div>
                );
              })}
              <div className="literary-filter-bar mt-3 pt-3 border-t border-[var(--literary-border)]">
                <button
                  type="button"
                  className={`filter-chip${!filter ? " filter-chip-active" : ""}`}
                  onClick={() => setFilter("")}
                >
                  🪶 Все {total > 0 && `(${total})`}
                </button>
              </div>
            </div>
          ) : (
            <div className="literary-filter-bar">
              <button
                type="button"
                className={`filter-chip${!filter ? " filter-chip-active" : ""}`}
                onClick={() => setFilter("")}
              >
                🪶 Все {total > 0 && `(${total})`}
              </button>
              {boardCategories.map(renderCategoryChip)}
            </div>
          )}
        </section>
      )}

      {showForm && (
        <ClassifiedAdForm
          mode="classifieds"
          categories={boardId === "help" ? boardCategories : categoriesForBoard("all", categories)}
          form={form}
          setForm={setForm}
          onSubmit={submit}
          formRef={formRef}
          submitting={submitting}
          showExtras={showExtras}
          onToggleExtras={() => setShowExtras(!showExtras)}
          kicker={formCopy.kicker}
          title={formCopy.title}
          freeTitle={formCopy.freeTitle}
          freeLead={boardId === "help" ? board.lead : formCopy.freeLead}
          agreeLabel={formCopy.agreeLabel}
          submitLabel={formCopy.submitLabel}
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
            msgType === "ok" && submittedId && submittedNotifyVk
              ? "Уведомим в VK, когда будет готово."
              : msgType === "ok" && submittedId
                ? "Укажите ВК в форме — пришлём сообщение в VK."
                : undefined
          }
          actions={
            msgType === "ok" && submittedId ? (
              <>
                <Link to={board.path} className="literary-link text-sm font-medium">
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

      {loadError && !loading && (
        <LiteraryEmptyState icon="⚠️" title="Доска временно недоступна" text="Не удалось загрузить объявления. Попробуйте ещё раз.">
          <button type="button" className="literary-btn literary-btn--primary mt-3" onClick={reload}>
            Повторить
          </button>
        </LiteraryEmptyState>
      )}

      {!loadError && (
        <div className="literary-classified-list">
          {ads.map((ad) => (
            <LiteraryClassifiedCard key={ad.id} ad={ad} compact />
          ))}
          {!loading && ads.length === 0 && (
            <LiteraryEmptyState {...emptyState}>
              <button type="button" className="literary-btn literary-btn--primary mt-2" onClick={() => setShowForm(true)}>
                + Подать объявление
              </button>
            </LiteraryEmptyState>
          )}
          {loading && ads.length === 0 && <LiteraryInlineLoader label="Загружаем объявления…" />}
          {loading && ads.length > 0 && <LiteraryInlineLoader label="Загружаем ещё…" />}
          {ads.length > 0 && ads.length < total && (
            <div className="text-center pt-4">
              <button type="button" className="literary-btn literary-btn--ghost" disabled={loading} onClick={loadMore}>
                Ещё объявления ({ads.length} из {total})
              </button>
            </div>
          )}
        </div>
      )}

      <div className="mt-8">
        <VkBotBanner />
      </div>
    </div>
  );
}
