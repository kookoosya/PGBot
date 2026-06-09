import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { VkBotBanner } from "@/components/VkBotLink";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd } from "@/lib/api";
import { BRAND } from "@/lib/branding";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { JOB_CATEGORY_IDS, JOB_FORM_HINTS, LOCAL_EMPLOYERS } from "@/lib/jobs";

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
  const [form, setForm] = useState({
    category: "job_tourism",
    title: "",
    description: "",
    price: "",
    price_unit: "₽/мес",
    phone: "",
    author_name: "",
    address: "",
    contact_vk: "",
    website_url: "",
    agree_rules: false,
  });
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");

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

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.createClassified({ ...form, price: form.price ? +form.price : undefined });
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
    <div className="page-section max-w-5xl">
      <PageHeader
        icon="💼"
        title="Работа в посёлке"
        subtitle={`${BRAND.name} и Пушкиногорский район — вакансии без посредников`}
      >
        <button type="button" className="btn-hero-primary text-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "✕ Отмена" : "+ Разместить вакансию"}
        </button>
        <span className="free-badge">🆓 Бесплатно</span>
      </PageHeader>

      <div className="human-note mb-6">
        <p className="m-0 text-sm">
          Здесь — только <strong>работа и подработка</strong>: музей, гостиницы, магазины, ЖКХ, сезонные дела.
          Дрова, покос и услуги мастеров — в{" "}
          <Link to="/classifieds" className="text-primary hover:underline">объявлениях</Link> и{" "}
          <Link to="/services" className="text-primary hover:underline">услугах</Link>.
        </p>
      </div>

      <section className="jobs-employers mb-8">
        <h2 className="text-lg font-bold mb-3">Кто нанимает в округе</h2>
        <div className="jobs-employers-grid">
          {LOCAL_EMPLOYERS.map((e) => (
            <div key={e.title} className="jobs-employer-card">
              <span className="jobs-employer-icon">{e.icon}</span>
              <div>
                <h3 className="text-sm font-bold m-0">{e.title}</h3>
                <p className="text-xs text-muted-foreground m-0 mt-1 leading-relaxed">{e.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="page-panel page-panel--gold mb-4">
        <div className="flex flex-col sm:flex-row gap-2">
          <Input
            placeholder="Поиск: продавец, водитель, лето…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
            className="flex-1"
          />
          <Button type="button" variant="outline" onClick={() => setSearch(searchInput.trim())}>
            Найти
          </Button>
        </div>
      </div>

      <div className="jobs-sector-filters mb-6">
        <button
          type="button"
          className={`classified-quick-btn ${!sector ? "classified-quick-btn-active" : ""}`}
          onClick={() => setSector("")}
        >
          Все вакансии {total > 0 && `(${total})`}
        </button>
        {jobCategories.map((c) => {
          const visual = getCategoryVisual(c.value);
          return (
            <button
              key={c.value}
              type="button"
              className={`classified-quick-btn ${sector === c.value ? "classified-quick-btn-active" : ""}`}
              onClick={() => setSector(c.value)}
            >
              {visual.icon} {c.label}
            </button>
          );
        })}
      </div>

      {showForm && (
        <form onSubmit={submit} className="pushkin-card p-6 mb-8 space-y-4 form-glow">
          <div className="free-banner">
            <span className="text-lg">🆓</span>
            <div>
              <p className="font-bold m-0">Бесплатная вакансия</p>
              <p className="text-sm text-muted-foreground m-0 mt-1">После модерации — на сайте и в VK-боте</p>
            </div>
          </div>
          <ul className="text-xs text-muted-foreground space-y-1 m-0 pl-4">
            {JOB_FORM_HINTS.map((h) => (
              <li key={h}>{h}</li>
            ))}
          </ul>
          <select
            className="pushkin-select w-full"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          >
            {jobCategories.map((c) => (
              <option key={c.value} value={c.value}>
                {getCategoryVisual(c.value).icon} {c.label}
              </option>
            ))}
          </select>
          <Input placeholder="Должность, напр. Продавец-кассир" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm min-h-[120px]"
            placeholder="Обязанности, график, требования, как связаться…"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-2">
            <Input type="number" placeholder="Зарплата / ставка" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
            <Input placeholder="за смену, месяц, сезон…" value={form.price_unit} onChange={(e) => setForm({ ...form, price_unit: e.target.value })} />
          </div>
          <Input placeholder="Телефон работодателя +7…" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <Input placeholder="Название организации или ФИО" value={form.author_name} onChange={(e) => setForm({ ...form, author_name: e.target.value })} required />
          <Input placeholder="Адрес / посёлок" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <Input placeholder="VK — уведомим о публикации" value={form.contact_vk} onChange={(e) => setForm({ ...form, contact_vk: e.target.value })} />
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
            <span>Вакансия настоящая, без предоплаты соискателям</span>
          </label>
          <Button type="submit" className="w-full">Отправить на модерацию</Button>
        </form>
      )}

      {msg && <p className={`mb-4 ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      <div className="epic-jobs-grid classified-jobs-list">
        {ads.map((ad) => {
          const visual = getCategoryVisual(ad.category);
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
                  📞 <span className="clickable-phone">{ad.phone}</span>
                  {ad.address && ` · 📍 ${ad.address}`}
                </p>
                <p className="text-xs text-muted-foreground mt-1">{ad.author_name}</p>
              </div>
            </Link>
          );
        })}
        {!loading && ads.length === 0 && (
          <div className="epic-job-empty col-span-full">
            <p>Вакансий пока нет — разместите первую, если ищете сотрудника.</p>
            <Button type="button" onClick={() => setShowForm(true)}>+ Разместить вакансию</Button>
          </div>
        )}
        {loading && <p className="text-center text-muted-foreground py-6 col-span-full">Загрузка…</p>}
        {ads.length > 0 && ads.length < total && (
          <div className="col-span-full text-center pt-4">
            <Button type="button" variant="outline" disabled={loading} onClick={() => load(page + 1, true)}>
              Ещё ({ads.length} из {total})
            </Button>
          </div>
        )}
      </div>

      <div className="mt-10">
        <VkBotBanner />
      </div>
    </div>
  );
}
