import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd, ClassifiedPaymentInfo } from "@/lib/api";
import { BRAND } from "@/lib/branding";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { PUSHKIN_QUOTES } from "@/lib/pushkin";

export function Classifieds() {
  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [payment, setPayment] = useState<ClassifiedPaymentInfo | null>(null);
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
    payment_confirmed: false,
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
    api.getClassifiedPaymentInfo().then(setPayment).catch(console.error);
    load();
  }, [filter]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.payment_confirmed) {
      setMsgType("err");
      setMsg(`Подтвердите оплату ${payment?.amount ?? 150} ₽ за размещение`);
      return;
    }
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
        payment_confirmed: false,
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
        {payment && (
          <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold bg-amber-400/20 border border-amber-400/40 text-amber-100">
            {payment.amount} ₽ / объявление / {payment.period_days} дн.
          </span>
        )}
      </PageHeader>

      <div className="human-note mb-6">
        <p className="m-0 text-sm">
          Объявление видят соседи по посёлку — дрова, вакансии, услуги.
          Размещение стоит <strong>150 ₽ на 30 дней</strong>: эти деньги идут на развитие портала, а не в карман посредникам.
        </p>
      </div>

      <div className="category-grid">
        <button
          type="button"
          className={`category-tile ${!filter ? "category-tile-active" : ""}`}
          onClick={() => setFilter("")}
        >
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
              <img src={visual.image} alt="" className="category-tile-img" loading="lazy" />
              <div className="category-tile-overlay" style={{ background: visual.gradient }} />
              <span className="category-tile-icon">{visual.icon}</span>
              <span className="category-tile-label">{c.label}</span>
            </button>
          );
        })}
      </div>

      {showForm && payment && (
        <form onSubmit={submit} className="pushkin-card p-6 mb-8 space-y-4">
          <div className="payment-box payment-box-simple">
            <p className="font-bold text-amber-900 text-lg mb-2">
              💳 {payment.amount} ₽ за объявление на {payment.period_days} дней
            </p>
            <p className="text-muted-foreground mb-4">{payment.message}</p>
            <div className="payment-card-number">
              {payment.card_number}
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              10 объявлений = 10 × {payment.amount} ₽. Каждое оплачивается отдельно.
            </p>
          </div>

          <select
            className="w-full border rounded px-3 py-2 text-sm"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          >
            {categories.map((c) => (
              <option key={c.value} value={c.value}>
                {getCategoryVisual(c.value).icon} {c.label}
              </option>
            ))}
          </select>
          <Input
            placeholder="Заголовок"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
          />
          <textarea
            className="w-full border rounded px-3 py-2 text-sm min-h-[100px]"
            placeholder="Описание"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-2">
            <Input
              type="number"
              placeholder="Ваша цена услуги"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
            />
            <Input
              placeholder="за что (м³, смена...)"
              value={form.price_unit}
              onChange={(e) => setForm({ ...form, price_unit: e.target.value })}
            />
          </div>
          <Input
            placeholder="Телефон"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            required
          />
          <Input
            placeholder="Ваше имя"
            value={form.author_name}
            onChange={(e) => setForm({ ...form, author_name: e.target.value })}
            required
          />
          <Input
            placeholder="Адрес / район"
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
          />
          <Input
            placeholder="ВКонтакте (id или ссылка) — для уведомления о публикации"
            value={form.contact_vk}
            onChange={(e) => setForm({ ...form, contact_vk: e.target.value })}
          />
          <label className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              className="mt-1"
              checked={form.payment_confirmed}
              onChange={(e) => setForm({ ...form, payment_confirmed: e.target.checked })}
            />
            <span>
              Я перевёл(а) <strong>{payment.amount} ₽</strong> на карту{" "}
              <strong className="font-mono">{payment.card_number}</strong>
            </span>
          </label>
          <Button type="submit" className="w-full">
            Отправить — уведомление придёт сразу
          </Button>
        </form>
      )}

      {msg && (
        <p className={`mb-4 ${msgType === "ok" ? "alert-success" : "alert-error"}`}>{msg}</p>
      )}

      <div className="space-y-4">
        {ads.map((ad) => {
          const visual = getCategoryVisual(ad.category);
          return (
            <div key={ad.id} className="classified-ad-card">
              <div className="classified-ad-image" style={{ background: visual.gradient }}>
                <img src={visual.image} alt="" loading="lazy" />
                <span className="classified-ad-badge">{visual.icon} {ad.category_label}</span>
              </div>
              <div className="classified-ad-body">
                <div className="flex justify-between gap-2">
                  <h3 className="font-bold text-lg">{ad.title}</h3>
                  {ad.price != null && (
                    <span className="text-amber-700 font-semibold shrink-0">
                      {ad.price} {ad.price_unit || "₽"}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{ad.author_name}</p>
                <p className="text-sm mt-2">{ad.description}</p>
                <p className="text-sm mt-3">
                  📞{" "}
                  <a href={`tel:${ad.phone.replace(/\s/g, "")}`} className="clickable-phone">
                    {ad.phone}
                  </a>
                  {ad.address && ` · 📍 ${ad.address}`}
                </p>
              </div>
            </div>
          );
        })}
        {ads.length === 0 && (
          <p className="text-center text-muted-foreground py-12">
            Объявлений пока нет. Будьте первым!
          </p>
        )}
      </div>
    </div>
  );
}
