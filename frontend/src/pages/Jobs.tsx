import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { VkBotBanner } from "@/components/VkBotLink";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { JOB_CATEGORY_IDS, JOB_FORM_HINTS, LOCAL_EMPLOYERS } from "@/lib/jobs";
import { EMPTY_STATES, LITERARY_VERSES, PAGE_SECTIONS } from "@/lib/literaryCopy";

const copy = PAGE_SECTIONS.jobs;

export function Jobs() {
  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
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
    <div className="literary-page page-section max-w-5xl">
      <PageHeader icon="💼" title={copy.title} subtitle={copy.lead}>
        <button type="button" className="literary-btn literary-btn--primary text-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "✕ Отмена" : "+ Разместить вакансию"}
        </button>
        <span className="free-badge">🆓 Бесплатно</span>
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
          {(search || sector) && (
            <button
              type="button"
              className="literary-btn literary-btn--ghost shrink-0 text-sm classified-quick-btn--reset"
              onClick={() => {
                setSearch("");
                setSearchInput("");
                setSector("");
              }}
            >
              Сбросить
            </button>
          )}
        </div>
      </section>

      <div className="literary-filter-bar mb-6">
        <button
          type="button"
          className={`classified-quick-btn ${!sector ? "classified-quick-btn-active" : ""}`}
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
              className={`classified-quick-btn ${sector === c.value ? "classified-quick-btn-active" : ""}`}
              onClick={() => setSector(c.value)}
            >
              {visual.icon} {c.label}
            </button>
          );
        })}
      </div>

      {showForm && (
        <form onSubmit={submit} className="page-panel page-panel--forest mb-8 space-y-4 form-glow literary-form-comfort">
          <LiterarySectionHead
            kicker={copy.form.kicker}
            title={copy.form.title}
            lead={copy.form.lead}
          />
          <div className="free-banner">
            <span className="text-lg">🆓</span>
            <div>
              <p className="font-bold m-0">Бесплатная вакансия</p>
              <p className="text-sm text-muted-foreground m-0 mt-1">После модерации — на сайте и в VK-боте</p>
            </div>
          </div>
          <ul className="literary-form-hints">
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
            className="literary-textarea w-full min-h-[120px]"
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
          <button type="submit" className="literary-btn literary-btn--primary w-full">
            Отправить на модерацию
          </button>
        </form>
      )}

      {msg && <p className={`mb-4 ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      <div className="literary-jobs-list">
        {loading && ads.length === 0 ? (
          <LiteraryInlineLoader label="Ищем вакансии в округе…" />
        ) : (
          ads.map((ad) => {
            const visual = getCategoryVisual(ad.category);
            return (
              <Link key={ad.id} to={`/classifieds/${ad.id}`} className="literary-job-card no-underline text-inherit">
                <div className="literary-job-icon" style={{ background: visual.gradient }}>
                  {visual.icon}
                </div>
                <div className="literary-job-body">
                  <span className="literary-job-badge">{ad.category_label}</span>
                  <h3 className="literary-job-title">{ad.title}</h3>
                  <p className="literary-job-desc">{ad.description}</p>
                  {ad.price != null && (
                    <p className="literary-job-pay">{ad.price} {ad.price_unit || "₽"}</p>
                  )}
                  <p className="literary-job-contact">
                    📞 <span className="clickable-phone">{ad.phone}</span>
                    {ad.address && ` · 📍 ${ad.address}`}
                  </p>
                </div>
              </Link>
            );
          })
        )}
        {!loading && ads.length === 0 && (
          <LiteraryEmptyState {...EMPTY_STATES.jobs}>
            <button type="button" className="literary-btn literary-btn--primary mt-2" onClick={() => setShowForm(true)}>
              + Разместить вакансию
            </button>
          </LiteraryEmptyState>
        )}
        {loading && ads.length > 0 && <LiteraryInlineLoader label="Обновляем список…" />}
        {ads.length > 0 && ads.length < total && (
          <div className="text-center pt-4">
            <button type="button" className="literary-btn literary-btn--ghost" disabled={loading} onClick={() => load(page + 1, true)}>
              Ещё ({ads.length} из {total})
            </button>
          </div>
        )}
      </div>

      <p className="literary-page-verse" aria-hidden>{LITERARY_VERSES.jobs}</p>

      <div className="mt-8">
        <VkBotBanner />
      </div>
    </div>
  );
}
