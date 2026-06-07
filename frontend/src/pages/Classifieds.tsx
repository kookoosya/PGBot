import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ClassifiedAd } from "@/lib/api";

export function Classifieds() {
  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [filter, setFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    category: "firewood", title: "", description: "", price: "", price_unit: "₽",
    phone: "", author_name: "", address: "",
  });
  const [msg, setMsg] = useState("");

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
      await api.createClassified({
        ...form,
        price: form.price ? +form.price : undefined,
      });
      setMsg("Объявление опубликовано!");
      setShowForm(false);
      load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Ошибка");
    }
  };

  const ICONS: Record<string, string> = {
    firewood: "🪵", grass_mowing: "🌿", delivery: "🚚", handyman: "🔧",
    snow_removal: "❄️", sale: "📦", job: "💼", other: "📋",
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold">📋 Объявления</h2>
        <p className="text-muted-foreground mt-2">Дрова, покос, доставка — жители помогают жителям</p>
      </div>

      <div className="flex flex-wrap gap-2 mb-6 justify-center">
        <Button size="sm" variant={!filter ? "default" : "outline"} onClick={() => setFilter("")}>Все</Button>
        {categories.map((c) => (
          <Button key={c.value} size="sm" variant={filter === c.value ? "default" : "outline"} onClick={() => setFilter(c.value)}>
            {ICONS[c.value] || "📋"} {c.label}
          </Button>
        ))}
        <Button size="sm" className="ml-auto" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Отмена" : "+ Подать объявление"}
        </Button>
      </div>

      {showForm && (
        <form onSubmit={submit} className="pushkin-card p-6 mb-8 space-y-3">
          <select className="w-full border rounded px-3 py-2 text-sm" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {categories.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          <Input placeholder="Заголовок" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <textarea className="w-full border rounded px-3 py-2 text-sm min-h-[100px]" placeholder="Описание" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          <div className="grid grid-cols-2 gap-2">
            <Input type="number" placeholder="Цена" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
            <Input placeholder="за что (м³, сотка...)" value={form.price_unit} onChange={(e) => setForm({ ...form, price_unit: e.target.value })} />
          </div>
          <Input placeholder="Телефон" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <Input placeholder="Ваше имя" value={form.author_name} onChange={(e) => setForm({ ...form, author_name: e.target.value })} required />
          <Input placeholder="Адрес / район" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <Button type="submit" className="w-full">Опубликовать</Button>
        </form>
      )}

      {msg && <p className="text-center text-sm text-green-700 mb-4">{msg}</p>}

      <div className="space-y-4">
        {ads.map((ad) => (
          <div key={ad.id} className="pushkin-card p-5">
            <div className="flex items-start gap-3">
              <span className="text-2xl">{ICONS[ad.category] || "📋"}</span>
              <div className="flex-1">
                <div className="flex justify-between">
                  <h3 className="font-bold">{ad.title}</h3>
                  {ad.price != null && <span className="text-amber-700 font-semibold">{ad.price} {ad.price_unit || "₽"}</span>}
                </div>
                <p className="text-xs text-muted-foreground">{ad.category_label} · {ad.author_name}</p>
                <p className="text-sm mt-2">{ad.description}</p>
                <p className="text-sm mt-2">📞 {ad.phone} {ad.address && `· 📍 ${ad.address}`}</p>
              </div>
            </div>
          </div>
        ))}
        {ads.length === 0 && (
          <p className="text-center text-muted-foreground py-12">
            Объявлений пока нет. Будьте первым!
          </p>
        )}
      </div>
    </div>
  );
}
