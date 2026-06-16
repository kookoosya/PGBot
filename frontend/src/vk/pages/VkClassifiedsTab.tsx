import { useCallback, useEffect, useState } from "react";
import { LiteraryClassifiedCard, LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd, ClassifiedMineAd } from "@/lib/api";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { VkErrorState } from "@/vk/components/VkErrorState";
import { VkSkeletonList } from "@/vk/components/VkSkeleton";
import { useAsyncData } from "@/vk/hooks/useAsyncData";
import { useVkAuth } from "@/vk/VkAuthContext";
import { useVkNavigation } from "@/vk/VkNavigationContext";
import { parseApiError } from "@/vk/lib/errors";

const MIN_TITLE = 3;
const MIN_DESC = 10;

const MINE_STATUS: Record<string, string> = {
  pending: "На модерации",
  approved: "Опубликовано",
  rejected: "Отклонено",
};

function mineStatusLabel(ad: ClassifiedMineAd): string {
  if (ad.payment_status === "approved" && ad.is_active) return "Опубликовано";
  if (ad.payment_status === "rejected") return "Отклонено";
  if (ad.payment_status === "pending") return "На модерации";
  return MINE_STATUS[ad.payment_status] || ad.payment_status;
}

export function VkClassifiedsTab() {
  const { user } = useVkAuth();
  const { openClassified } = useVkNavigation();
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [showMine, setShowMine] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [form, setForm] = useState({
    category: "firewood",
    title: "",
    description: "",
    phone: "",
    author_name: "",
    agree_rules: false,
  });

  useEffect(() => {
    if (user) {
      setForm((f) => ({
        ...f,
        author_name: f.author_name || user.full_name || "",
        phone: f.phone || user.phone || "",
      }));
    }
  }, [user]);

  const loader = useCallback(async () => {
    const params: Record<string, string> = { ads_only: "true", page_size: "20" };
    if (search) params.search = search;
    const r = await api.getClassifieds(params);
    return r.items;
  }, [search]);

  const mineLoader = useCallback(async () => {
    if (!user) return [];
    const r = await api.getMyClassifieds({ page_size: "30" });
    return r.items;
  }, [user]);

  const { data: ads, loading, error, reload } = useAsyncData<ClassifiedAd[]>(loader, [search]);
  const {
    data: myAds,
    loading: mineLoading,
    error: mineError,
    reload: reloadMine,
  } = useAsyncData<ClassifiedMineAd[]>(mineLoader, [user?.id], { enabled: Boolean(user && showMine) });

  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(searchInput.trim()), 400);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const validateForm = (): string | null => {
    if (form.title.trim().length < MIN_TITLE) return `Заголовок — минимум ${MIN_TITLE} символа`;
    if (form.description.trim().length < MIN_DESC) return `Описание — минимум ${MIN_DESC} символов`;
    if (!/^\+?\d[\d\s()-]{8,}$/.test(form.phone.trim())) return "Укажите телефон в формате +7…";
    if (!form.author_name.trim()) return "Укажите имя";
    if (!form.agree_rules) return "Подтвердите честность объявления";
    return null;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg("");
    const validationError = validateForm();
    if (validationError) {
      setMsgType("err");
      setMsg(validationError);
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.createClassified({
        ...form,
        title: form.title.trim(),
        description: form.description.trim(),
        phone: form.phone.trim(),
        author_name: form.author_name.trim(),
      });
      setMsgType("ok");
      setMsg(res.message);
      setShowForm(false);
      setForm((f) => ({ ...f, title: "", description: "", agree_rules: false }));
      reload();
      if (showMine) reloadMine();
    } catch (err) {
      setMsgType("err");
      setMsg(parseApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="vk-tab-panel">
      <LiterarySectionHead kicker="📋 Объявления" title="Доска соседей" lead="Дрова, услуги, аренда — бесплатно." />

      <div className="vk-search-row">
        <Input
          placeholder="Поиск по заголовку…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="pushkin-select flex-1"
        />
      </div>

      <div className="vk-filter-row">
        <button type="button" className="literary-btn literary-btn--primary flex-1" onClick={() => setShowForm(!showForm)}>
          {showForm ? "✕ Закрыть форму" : "+ Подать объявление"}
        </button>
        {user && (
          <button
            type="button"
            className={`literary-btn literary-btn--ghost flex-1${showMine ? " literary-btn--active" : ""}`}
            onClick={() => setShowMine(!showMine)}
          >
            {showMine ? "Все объявления" : "Мои объявления"}
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={submit} className="page-panel page-panel--forest space-y-3 literary-form-comfort">
          <p className="text-xs text-muted-foreground m-0">Заголовок от 3 символов, описание от 10. Телефон нужен для связи соседей.</p>
          <select
            className="pushkin-select w-full"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          >
            <option value="firewood">🪵 Дрова</option>
            <option value="mowing">🌿 Покос</option>
            <option value="sale">🏷 Продажа</option>
            <option value="rent">🏠 Аренда</option>
            <option value="neighbor_help">🤝 Сосед помогает</option>
          </select>
          <Input
            placeholder="Заголовок"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
            minLength={MIN_TITLE}
          />
          <textarea
            className="literary-textarea w-full min-h-[90px]"
            placeholder="Описание (что продаёте или предлагаете)"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
            minLength={MIN_DESC}
          />
          <Input placeholder="Телефон +7…" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <Input placeholder="Ваше имя" value={form.author_name} onChange={(e) => setForm({ ...form, author_name: e.target.value })} required />
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.agree_rules}
              onChange={(e) => setForm({ ...form, agree_rules: e.target.checked })}
              className="mt-1"
              required
            />
            <span>Объявление честное, без предоплаты незнакомцам.</span>
          </label>
          <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={submitting}>
            {submitting ? "Отправляем…" : "Отправить на модерацию"}
          </button>
        </form>
      )}

      {msg && <p className={`text-sm ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      {showMine ? (
        mineLoading ? (
          <VkSkeletonList count={3} />
        ) : mineError ? (
          <VkErrorState message={mineError} onRetry={reloadMine} />
        ) : !myAds?.length ? (
          <LiteraryEmptyState icon="📋" title="Пока нет объявлений" text="Подайте первое — оно появится здесь после модерации." compact />
        ) : (
          <div className="literary-classified-list">
            {myAds.map((ad) => (
              <div key={ad.id} className="vk-mine-ad-wrap">
                <span className={`vk-mine-status vk-mine-status--${ad.payment_status}`}>{mineStatusLabel(ad)}</span>
                <LiteraryClassifiedCard ad={ad} compact onOpen={() => openClassified(ad.id)} />
              </div>
            ))}
          </div>
        )
      ) : loading ? (
        <VkSkeletonList count={4} />
      ) : error ? (
        <VkErrorState message={error} onRetry={reload} />
      ) : !ads?.length ? (
        <LiteraryEmptyState {...EMPTY_STATES.classifieds} compact />
      ) : (
        <div className="literary-classified-list">
          {ads.map((ad) => (
            <LiteraryClassifiedCard key={ad.id} ad={ad} compact onOpen={() => openClassified(ad.id)} />
          ))}
        </div>
      )}
    </section>
  );
}
