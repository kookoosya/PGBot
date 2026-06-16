import { useEffect, useState } from "react";
import { LiteraryClassifiedCard, LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd } from "@/lib/api";
import { EMPTY_STATES } from "@/lib/literaryCopy";

export function VkClassifiedsTab() {
  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
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

  const load = () => {
    setLoading(true);
    api
      .getClassifieds({ ads_only: "true", page_size: "20" })
      .then((r) => setAds(r.items))
      .catch(() => setAds([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg("");
    try {
      const res = await api.createClassified(form);
      setMsgType("ok");
      setMsg(res.message);
      setShowForm(false);
      setForm((f) => ({ ...f, title: "", description: "", agree_rules: false }));
      load();
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Ошибка отправки");
    }
  };

  return (
    <section className="vk-tab-panel">
      <LiterarySectionHead
        kicker="📋 Объявления"
        title="Доска соседей"
        lead="Дрова, услуги, аренда — бесплатно."
      />
      <button type="button" className="literary-btn literary-btn--primary w-full mb-4" onClick={() => setShowForm(!showForm)}>
        {showForm ? "✕ Закрыть форму" : "+ Подать объявление"}
      </button>

      {showForm && (
        <form onSubmit={submit} className="page-panel page-panel--forest mb-4 space-y-3 literary-form-comfort">
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
            placeholder="Описание"
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
          <button type="submit" className="literary-btn literary-btn--primary w-full">
            Отправить на модерацию
          </button>
        </form>
      )}

      {msg && <p className={`text-sm mb-3 ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      {loading ? (
        <LiteraryInlineLoader label="Загружаем объявления…" compact />
      ) : ads.length === 0 ? (
        <LiteraryEmptyState {...EMPTY_STATES.classifieds} compact />
      ) : (
        <div className="literary-classified-list">
          {ads.map((ad) => (
            <LiteraryClassifiedCard key={ad.id} ad={ad} compact />
          ))}
        </div>
      )}
    </section>
  );
}
