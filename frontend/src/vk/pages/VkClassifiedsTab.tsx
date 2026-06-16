import { useCallback, useEffect, useState } from "react";
import { LiteraryClassifiedCard, LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd } from "@/lib/api";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { VkErrorState } from "@/vk/components/VkErrorState";
import { useVkAuth } from "@/vk/VkAuthContext";
import { useVkNavigation } from "@/vk/VkNavigationContext";
import { parseApiError } from "@/vk/lib/errors";

const MIN_TITLE = 3;
const MIN_DESC = 10;

export function VkClassifiedsTab() {
  const { user } = useVkAuth();
  const { openClassified } = useVkNavigation();
  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
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

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    const params: Record<string, string> = { ads_only: "true", page_size: "20" };
    if (search) params.search = search;
    api
      .getClassifieds(params)
      .then((r) => setAds(r.items))
      .catch((err) => {
        setAds([]);
        setError(parseApiError(err));
      })
      .finally(() => setLoading(false));
  }, [search]);

  useEffect(() => {
    load();
  }, [load]);

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
      load();
    } catch (err) {
      setMsgType("err");
      setMsg(parseApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="vk-tab-panel">
      <LiterarySectionHead
        kicker="📋 Объявления"
        title="Доска соседей"
        lead="Дрова, услуги, аренда — бесплатно."
      />

      <div className="vk-search-row">
        <Input
          placeholder="Поиск по заголовку…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
          className="pushkin-select flex-1"
        />
        <button type="button" className="literary-btn literary-btn--ghost shrink-0" onClick={() => setSearch(searchInput.trim())}>
          Найти
        </button>
      </div>

      <button type="button" className="literary-btn literary-btn--primary w-full" onClick={() => setShowForm(!showForm)}>
        {showForm ? "✕ Закрыть форму" : "+ Подать объявление"}
      </button>

      {showForm && (
        <form onSubmit={submit} className="page-panel page-panel--forest space-y-3 literary-form-comfort">
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
          <Input placeholder="Заголовок" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <textarea
            className="literary-textarea w-full min-h-[90px]"
            placeholder="Описание (что продаёте или предлагаете)"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
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

      {loading ? (
        <LiteraryInlineLoader label="Загружаем объявления…" compact />
      ) : error ? (
        <VkErrorState message={error} onRetry={load} />
      ) : ads.length === 0 ? (
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
