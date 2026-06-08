import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { VkBotBanner } from "@/components/VkBotLink";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd } from "@/lib/api";
import { BRAND } from "@/lib/branding";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { PUSHKIN_QUOTES } from "@/lib/pushkin";

const JOB_CATEGORIES = new Set(["job", "construction_vacancy"]);

export function Classifieds() {
  const [searchParams] = useSearchParams();
  const jobsMode = searchParams.get("jobs") === "1";

  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [filter, setFilter] = useState(jobsMode ? "job" : "");
  const [jobsOnly, setJobsOnly] = useState(jobsMode);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    category: jobsMode ? "job" : "firewood",
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

  const load = (pageNum = 1, append = false) => {
    const params: Record<string, string> = {
      page: String(pageNum),
      page_size: "20",
    };
    if (jobsOnly) {
      params.jobs_only = "true";
    } else if (filter) {
      params.category = filter;
    }
    if (search) params.search = search;
    setLoading(true);
    api.getClassifieds(params)
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
    if (jobsMode) {
      setJobsOnly(true);
      setFilter("");
      setForm((f) => ({ ...f, category: "job" }));
    }
  }, [jobsMode]);

  useEffect(() => {
    load(1, false);
  }, [filter, jobsOnly, search]);

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

  const visibleCategories = jobsOnly
    ? categories.filter((c) => JOB_CATEGORIES.has(c.value))
    : categories;

  return (
    <div className="page-section max-w-5xl">
      <PageHeader
        icon={jobsOnly ? "💼" : "📋"}
        title={jobsOnly ? "Работа и вакансии" : "Доска объявлений"}
        subtitle={
          jobsOnly
            ? `${BRAND.name} — вакансии и подработка от соседей`
            : `${BRAND.name} — «${PUSHKIN_QUOTES.classifieds.replace(/«|»/g, "")}»`
        }
      >
        <button type="button" className="btn-hero-primary text-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "✕ Отмена" : jobsOnly ? "+ Вакансия" : "+ Подать объявление"}
        </button>
        <span className="free-badge">🆓 Бесплатно</span>
      </PageHeader>

      <div className="human-note mb-6">
        <p className="m-0 text-sm">
          Размещение <strong>бесплатно и без регистрации</strong> — после модерации объявление появится на портале и в VK-боте.
          Не переводите предоплату незнакомцам: все сделки — лично или по телефону.
          Услуги (огород, дрова, мастера) — на{" "}
          <Link to="/services" className="text-primary hover:underline">странице «Услуги»</Link>.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-2 mb-4">
        <Input
          placeholder="Поиск по заголовку…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
          className="flex-1"
        />
        <Button type="button" variant="outline" onClick={() => setSearch(searchInput.trim())}>
          Найти
        </Button>
      </div>

      <div className="classified-quick-filters mb-4">
        <button
          type="button"
          className={`classified-quick-btn ${!jobsOnly && !filter ? "classified-quick-btn-active" : ""}`}
          onClick={() => { setJobsOnly(false); setFilter(""); }}
        >
          Все объявления
        </button>
        <button
          type="button"
          className={`classified-quick-btn ${jobsOnly ? "classified-quick-btn-active" : ""}`}
          onClick={() => { setJobsOnly(true); setFilter(""); setForm((f) => ({ ...f, category: "job" })); }}
        >
          💼 Работа и вакансии
        </button>
      </div>

      {!jobsOnly && (
        <div className="category-grid">
          <button type="button" className={`category-tile ${!filter ? "category-tile-active" : ""}`} onClick={() => setFilter("")}>
            <div className="category-tile-bg" style={{ background: "linear-gradient(135deg, #1a4d3a, #2d6a4f)" }} />
            <span className="category-tile-icon">🪶</span>
            <span className="category-tile-label">Все</span>
          </button>
          {categories.map((c) => {
            const visual = getCategoryVisual(c.value);
            return (
              <button
                key={c.value}
                type="button"
                className={`category-tile ${filter === c.value ? "category-tile-active" : ""}`}
                onClick={() => setFilter(c.value)}
              >
                <div className="category-tile-bg" style={{ background: visual.gradient }} />
                <span className="category-tile-icon">{visual.icon}</span>
                <span className="category-tile-label">{c.label}</span>
              </button>
            );
          })}
        </div>
      )}

      {showForm && (
        <form onSubmit={submit} className="pushkin-card p-6 mb-8 space-y-4 form-glow">
          <div className="free-banner">
            <span className="text-lg">🆓</span>
            <div>
              <p className="font-bold m-0">Бесплатное размещение</p>
              <p className="text-sm text-muted-foreground m-0 mt-1">Регистрация не нужна. Проверим и опубликуем после модерации.</p>
            </div>
          </div>

          <div className="antifraud-note">
            <p className="m-0 text-sm">
              <strong>Без обмана:</strong> не просите предоплату, залог и переводы на карту.
              Модератор отклонит подозрительные объявления.
            </p>
          </div>

          <select className="w-full border rounded-lg px-3 py-2 text-sm" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {(jobsOnly ? visibleCategories : categories).map((c) => (
              <option key={c.value} value={c.value}>{getCategoryVisual(c.value).icon} {c.label}</option>
            ))}
          </select>
          <Input placeholder="Заголовок" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm min-h-[100px]"
            placeholder="Описание"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-2">
            <Input type="number" placeholder={jobsOnly ? "Зарплата / ставка" : "Ваша цена"} value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
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
          <p className="text-xs text-muted-foreground m-0 -mt-2">
            Необязательно. После модерации пришлём сообщение в VK, если указали профиль.
          </p>
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
            <span>
              Объявление честное: без предоплаты, залога и переводов незнакомцам. Контакты настоящие.
            </span>
          </label>
          <Button type="submit" className="w-full">🆓 Отправить на модерацию</Button>
        </form>
      )}

      {msg && <p className={`mb-4 ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      <div className="mb-8">
        <VkBotBanner />
      </div>

      <div className={jobsOnly ? "epic-jobs-grid classified-jobs-list" : "space-y-4"}>
        {ads.map((ad) => {
          const visual = getCategoryVisual(ad.category);
          if (jobsOnly) {
            return (
              <Link key={ad.id} to={`/classifieds/${ad.id}`} className="epic-job-card no-underline text-inherit">
                <div className="epic-job-icon" style={{ background: visual.gradient }}>
                  {visual.icon}
                </div>
                <div className="epic-job-body">
                  <span className="epic-job-badge">{ad.category_label}</span>
                  <h3 className="epic-job-title">{ad.title}</h3>
                  <p className="epic-job-desc">{ad.description}</p>
                  {ad.price != null && (
                    <p className="epic-job-pay">{ad.price} {ad.price_unit || "₽"}</p>
                  )}
                  <p className="epic-job-contact">
                    📞 <a href={`tel:${ad.phone.replace(/\s/g, "")}`} className="clickable-phone">{ad.phone}</a>
                    {ad.address && ` · 📍 ${ad.address}`}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">{ad.author_name}</p>
                </div>
              </Link>
            );
          }
          return (
            <div key={ad.id} className="classified-ad-card">
              <div className="classified-ad-image" style={{ background: visual.gradient }}>
                <span className="classified-ad-icon">{visual.icon}</span>
                <span className="classified-ad-badge">{ad.category_label}</span>
              </div>
              <div className="classified-ad-body">
                <div className="flex justify-between gap-2">
                  <h3 className="font-bold text-lg">
                    <Link to={`/classifieds/${ad.id}`} className="hover:underline">{ad.title}</Link>
                  </h3>
                  {ad.price != null && (
                    <span className="text-amber-700 font-semibold shrink-0">{ad.price} {ad.price_unit || "₽"}</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{ad.author_name}</p>
                <p className="text-sm mt-2">{ad.description}</p>
                <p className="text-sm mt-3">
                  📞 <a href={`tel:${ad.phone.replace(/\s/g, "")}`} className="clickable-phone">{ad.phone}</a>
                  {ad.address && ` · 📍 ${ad.address}`}
                </p>
              </div>
            </div>
          );
        })}
        {!loading && ads.length === 0 && (
          <p className="text-center text-muted-foreground py-12 col-span-full">
            {jobsOnly ? "Вакансий пока нет. Разместите первую!" : "Объявлений пока нет. Будьте первым!"}
          </p>
        )}
        {loading && <p className="text-center text-muted-foreground py-6 col-span-full">Загрузка…</p>}
        {ads.length > 0 && ads.length < total && (
          <div className="col-span-full text-center pt-4">
            <Button type="button" variant="outline" disabled={loading} onClick={() => load(page + 1, true)}>
              Ещё объявления ({ads.length} из {total})
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
