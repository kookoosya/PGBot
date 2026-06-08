import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, CatalogItemAdmin, CatalogItemCreate } from "@/lib/api";

const CATEGORIES = [
  { value: "garden", label: "Огород / дача" },
  { value: "firewood", label: "Дрова" },
  { value: "grass_mowing", label: "Покос" },
  { value: "handyman", label: "Разные работы" },
  { value: "construction", label: "Строительство" },
  { value: "delivery", label: "Доставка" },
  { value: "snow_removal", label: "Снег" },
  { value: "tutoring", label: "Обучение" },
  { value: "other", label: "Другое" },
];

const emptyForm: CatalogItemCreate = {
  name: "",
  category: "other",
  description: "",
  phone: "",
  external_url: "",
  price_hint: "",
  address: "",
  is_internal: true,
  sort_order: 10,
};

export function AdminProposals() {
  const [items, setItems] = useState<CatalogItemAdmin[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<CatalogItemCreate>(emptyForm);
  const [tab, setTab] = useState<"internal" | "all">("internal");
  const [msg, setMsg] = useState("");

  const load = () => {
    api.getAdminCatalogItems(tab === "internal").then(setItems).catch(console.error);
  };

  useEffect(() => { load(); }, [tab]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCatalogItem(form);
      setForm(emptyForm);
      setShowForm(false);
      setMsg("Добавлено");
      load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Ошибка");
    }
  };

  const toggleActive = async (item: CatalogItemAdmin) => {
    await api.updateCatalogItem(item.id, { is_active: !item.is_active } as Partial<CatalogItemCreate>);
    load();
  };

  const internalItems = items.filter((i) => i.is_internal);
  const publicRef = items.filter((i) => !i.is_internal);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between gap-4 items-start">
        <div>
          <h2 className="text-3xl font-bold">Предложения и справочник</h2>
          <p className="text-muted-foreground">
            Внутренние записи видны только вам. Публичный справочник — на странице «Услуги».
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Отмена" : "+ Добавить"}</Button>
      </div>

      <div className="flex gap-2">
        <Button size="sm" variant={tab === "internal" ? "default" : "outline"} onClick={() => setTab("internal")}>
          🔒 Только для админа ({internalItems.length})
        </Button>
        <Button size="sm" variant={tab === "all" ? "default" : "outline"} onClick={() => setTab("all")}>
          Весь справочник ({items.length})
        </Button>
      </div>

      {msg && <p className="text-sm text-green-700">{msg}</p>}

      {showForm && (
        <Card className="pushkin-card">
          <CardContent className="p-6">
            <form onSubmit={submit} className="space-y-3 max-w-lg">
              <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Название" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              <select className="w-full border rounded px-3 py-2 text-sm" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
              <textarea className="w-full border rounded px-3 py-2 text-sm min-h-[80px]" placeholder="Описание" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Телефон" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Ссылка (сайт)" value={form.external_url} onChange={(e) => setForm({ ...form, external_url: e.target.value })} />
              <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Цена / подсказка" value={form.price_hint} onChange={(e) => setForm({ ...form, price_hint: e.target.value })} />
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.is_internal !== false} onChange={(e) => setForm({ ...form, is_internal: e.target.checked })} />
                Только для админа (не показывать на сайте)
              </label>
              <Button type="submit">Сохранить</Button>
            </form>
          </CardContent>
        </Card>
      )}

      {tab === "internal" && internalItems.length === 0 && (
        <Card><CardContent className="py-10 text-center text-muted-foreground">
          Нет внутренних предложений. Добавьте заметки, идеи, контакты — их не увидят жители.
        </CardContent></Card>
      )}

      {(tab === "internal" ? internalItems : items).map((item) => (
        <Card key={item.id} className={`pushkin-card ${!item.is_active ? "opacity-50" : ""}`}>
          <CardContent className="p-6 flex flex-wrap justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-semibold">{item.name}</h3>
                {item.is_internal && <span className="text-xs bg-amber-100 text-amber-900 px-2 py-0.5 rounded">🔒 админ</span>}
                {!item.is_active && <span className="text-xs bg-gray-200 px-2 py-0.5 rounded">выкл</span>}
              </div>
              <p className="text-sm text-muted-foreground">{item.category_label} · {item.source}</p>
              {item.description && <p className="text-sm mt-2">{item.description}</p>}
              {item.phone && <p className="text-sm">📞 {item.phone}</p>}
              {item.external_url && (
                <a href={item.external_url} target="_blank" rel="noreferrer" className="text-sm text-primary">{item.external_url}</a>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Button size="sm" variant="outline" onClick={() => toggleActive(item)}>
                {item.is_active ? "Скрыть" : "Включить"}
              </Button>
              {!item.seed_key && (
                <Button size="sm" variant="destructive" onClick={async () => { await api.deleteCatalogItem(item.id); load(); }}>
                  Удалить
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}

      {tab === "all" && publicRef.length > 0 && (
        <p className="text-xs text-muted-foreground">
          Публичных записей из справочника: {publicRef.length} (обновляются при синке карты)
        </p>
      )}
    </div>
  );
}
