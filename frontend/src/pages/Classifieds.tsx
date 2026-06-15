import { useEffect, useState } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryClassifiedCard, LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { VkBotBanner } from "@/components/VkBotLink";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { JOB_CATEGORY_IDS } from "@/lib/jobs";
import { EMPTY_STATES, LITERARY_VERSES, PAGE_SECTIONS } from "@/lib/literaryCopy";

export function Classifieds() {
  const [searchParams] = useSearchParams();
  const neighborMode = searchParams.get("neighbor") === "1";
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
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    category: "firewood",
    title: "",
    description: "",
    price: "",
    price_unit: "₽",
    phone: "",
    author_name: "",
    address: "",
    contact_vk: "",
    website_url: "",
    agree_rules: false,
  });
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");

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
    api.getClassifiedCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    load(1, false);
  }, [filter, search, neighborMode]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.createClassified({
        ...form,
        price: form.price ? +form.price : undefined,
      });
      setMsgType("ok");
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
      load(1, false);
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Ошибка");
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
        <span className="free-badge">🆓 Бесплатно</span>
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
          lead="Введите слово из заголовка или описания."
        />
        <div className="flex flex-col sm:flex-row gap-2">
          <Input
            placeholder="Поиск по заголовку…"
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
          className={`classified-quick-btn ${!filter ? "classified-quick-btn-active" : ""}`}
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
              className={`classified-quick-btn ${filter === c.value ? "classified-quick-btn-active" : ""}`}
              onClick={() => setFilter(c.value)}
            >
              {visual.icon} {c.label}
            </button>
          );
        })}
      </div>

      {showForm && (
        <form onSubmit={submit} className="page-panel page-panel--forest mb-8 space-y-4 form-glow">
          <LiterarySectionHead
            kicker="✍️ Новое объявление"
            title="Подать на модерацию"
            lead="Регистрация не нужна. Проверим и опубликуем в течение суток."
          />
          <div className="free-banner">
            <span className="text-lg">🆓</span>
            <div>
              <p className="font-bold m-0">Бесплатное размещение</p>
              <p className="text-sm text-muted-foreground m-0 mt-1">Честные объявления — без предоплаты и переводов незнакомцам.</p>
            </div>
          </div>

          <select className="pushkin-select w-full" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {adCategories.map((c) => (
              <option key={c.value} value={c.value}>{getCategoryVisual(c.value).icon} {c.label}</option>
            ))}
          </select>
          <Input placeholder="Заголовок" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <textarea
            className="literary-textarea w-full min-h-[100px]"
            placeholder="Описание"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-2">
            <Input type="number" placeholder="Ваша цена" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
            <Input placeholder="за что (смена, месяц…)" value={form.price_unit} onChange={(e) => setForm({ ...form, price_unit: e.target.value })} />
          </div>
          <Input placeholder="Телефон +7…" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <Input placeholder="Ваше имя" value={form.author_name} onChange={(e) => setForm({ ...form, author_name: e.target.value })} required />
          <Input placeholder="Адрес / район" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <Input
            placeholder="ВКонтакте (id или ссылка) — уведомим, когда опубликуем"
            value={form.contact_vk}
            onChange={(e) => setForm({ ...form, contact_vk: e.target.value })}
          />
          <input
            type="text"
            name="website_url"
            value={form.website_url}
            onChange={(e) => setForm({ ...form, website_url: e.target.value })}
            className="honeypot-field"
            tabIndex={-1}
            autoComplete="off"
            aria-hidden
          />
          <label className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={form.agree_rules}
              onChange={(e) => setForm({ ...form, agree_rules: e.target.checked })}
              className="mt-1"
              required
            />
            <span>Объявление честное: без предоплаты и переводов незнакомцам.</span>
          </label>
          <button type="submit" className="literary-btn literary-btn--primary w-full">
            🆓 Отправить на модерацию
          </button>
        </form>
      )}

      {msg && <p className={`mb-4 ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      <div className="mb-8">
        <VkBotBanner />
      </div>

      <div className="literary-classified-list">
        {ads.map((ad) => (
          <LiteraryClassifiedCard key={ad.id} ad={ad} />
        ))}
        {!loading && ads.length === 0 && (
          <LiteraryEmptyState {...EMPTY_STATES.classifieds}>
            <button type="button" className="literary-btn literary-btn--primary mt-2" onClick={() => setShowForm(true)}>
              + Подать объявление
            </button>
          </LiteraryEmptyState>
        )}
        {loading && <p className="landing-muted text-center py-6">Загрузка…</p>}
        {ads.length > 0 && ads.length < total && (
          <div className="text-center pt-4">
            <button type="button" className="literary-btn literary-btn--ghost" disabled={loading} onClick={() => load(page + 1, true)}>
              Ещё объявления ({ads.length} из {total})
            </button>
          </div>
        )}
      </div>

      <p className="landing-section-verse text-center mt-8" aria-hidden>{LITERARY_VERSES.classifieds}</p>
    </div>
  );
}
