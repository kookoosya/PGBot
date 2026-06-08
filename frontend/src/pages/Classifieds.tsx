import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd } from "@/lib/api";
import { BRAND } from "@/lib/branding";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { PUSHKIN_QUOTES } from "@/lib/pushkin";

export function Classifieds() {
  const [ads, setAds] = useState<ClassifiedAd[]>([]);
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
  });
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");

  const load = () => {
    const params: Record<string, string> = {};
    if (filter) params.category = filter;
    api.getClassifieds(params).then((r) => setAds(r.items)).catch(console.error);
  };

  useEffect(() => {
    api.getClassifiedCategories().then(setCategories).catch(console.error);
    load();
  }, [filter]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.createClassified({
        ...form,
        price: form.price ? +form.price : undefined,
        payment_confirmed: true,
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
      }));
      load();
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Ошибка");
    }
  };

  return (
    <div className="page-section max-w-5xl">
      <PageHeader
        icon="📋"
        title="Доска объявлений"
        subtitle={`${BRAND.name} — «${PUSHKIN_QUOTES.classifieds.replace(/«|»/g, "")}»`}
      >
        <button type="button" className="btn-hero-primary text-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "✕ Отмена" : "+ Подать объявление"}
        </button>
        <span className="free-badge">🆓 Бесплатно</span>
      </PageHeader>

      <div className="human-note mb-6">
        <p className="m-0 text-sm">
          Размещение объявлений <strong>бесплатно</strong> — после модерации появится на портале и в VK-боте.
          Услуги (огород, дрова, мастера) — на{" "}
          <Link to="/services" className="text-primary hover:underline">странице «Услуги»</Link>.
          Платный только <Link to="/ai" className="text-primary hover:underline">ИИ-помощник</Link> после дневного лимита.
        </p>
      </div>

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

      {showForm && (
        <form onSubmit={submit} className="pushkin-card p-6 mb-8 space-y-4 form-glow">
          <div className="free-banner">
            <span className="text-lg">🆓</span>
            <div>
              <p className="font-bold m-0">Бесплатное размещение</p>
              <p className="text-sm text-muted-foreground m-0 mt-1">Проверим и опубликуем после модерации</p>
            </div>
          </div>

          <select className="w-full border rounded-lg px-3 py-2 text-sm" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {categories.map((c) => (
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
            <Input type="number" placeholder="Ваша цена" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
            <Input placeholder="за что (м³, смена…)" value={form.price_unit} onChange={(e) => setForm({ ...form, price_unit: e.target.value })} />
          </div>
          <Input placeholder="Телефон" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <Input placeholder="Ваше имя" value={form.author_name} onChange={(e) => setForm({ ...form, author_name: e.target.value })} required />
          <Input placeholder="Адрес / район" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <Input
            placeholder="ВКонтакте — для уведомления о публикации"
            value={form.contact_vk}
            onChange={(e) => setForm({ ...form, contact_vk: e.target.value })}
          />
          <Button type="submit" className="w-full">🆓 Отправить на модерацию</Button>
        </form>
      )}

      {msg && <p className={`mb-4 ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>}

      <div className="space-y-4">
        {ads.map((ad) => {
          const visual = getCategoryVisual(ad.category);
          return (
            <div key={ad.id} className="classified-ad-card">
              <div className="classified-ad-image" style={{ background: visual.gradient }}>
                <span className="classified-ad-icon">{visual.icon}</span>
                <span className="classified-ad-badge">{ad.category_label}</span>
              </div>
              <div className="classified-ad-body">
                <div className="flex justify-between gap-2">
                  <h3 className="font-bold text-lg">{ad.title}</h3>
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
        {ads.length === 0 && (
          <p className="text-center text-muted-foreground py-12">Объявлений пока нет. Будьте первым!</p>
        )}
      </div>
    </div>
  );
}
