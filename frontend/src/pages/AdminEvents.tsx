import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, EventCreate, EventItem } from "@/lib/api";

const CATEGORIES = [
  { value: "culture", label: "Культура" },
  { value: "holiday", label: "Праздник" },
  { value: "sport", label: "Спорт" },
  { value: "education", label: "Образование" },
  { value: "community", label: "Общее" },
  { value: "tourism", label: "Туризм" },
  { value: "other", label: "Другое" },
];

function toLocalInputValue(iso: string | null | undefined): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function fromLocalInputValue(value: string): string {
  if (!value) return "";
  return new Date(value).toISOString();
}

const emptyForm: EventCreate = {
  title: "",
  description: "",
  starts_at: "",
  ends_at: "",
  location: "",
  category: "culture",
  source: "manual",
  source_url: "",
  is_published: true,
};

export function AdminEvents() {
  const [items, setItems] = useState<EventItem[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<EventCreate>(emptyForm);
  const [editId, setEditId] = useState<number | null>(null);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    api
      .getAdminEvents(true)
      .then((response) => setItems(response.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Ошибка загрузки"));
  };

  useEffect(() => {
    load();
  }, []);

  const resetForm = () => {
    setForm(emptyForm);
    setEditId(null);
    setShowForm(false);
  };

  const startEdit = (event: EventItem) => {
    setEditId(event.id);
    setForm({
      title: event.title,
      description: event.description || "",
      starts_at: event.starts_at,
      ends_at: event.ends_at,
      location: event.location || "",
      category: event.category,
      source: event.source || "manual",
      source_url: event.source_url || "",
      is_published: event.is_published,
    });
    setShowForm(true);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setMsg("");
    setError("");
    const payload: EventCreate = {
      ...form,
      starts_at: fromLocalInputValue(toLocalInputValue(form.starts_at) || form.starts_at),
      ends_at: form.ends_at ? fromLocalInputValue(toLocalInputValue(form.ends_at) || form.ends_at) : null,
    };
    try {
      if (editId) {
        await api.updateEvent(editId, payload);
        setMsg("Событие обновлено");
      } else {
        await api.createEvent(payload);
        setMsg("Событие добавлено");
      }
      resetForm();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    }
  };

  const togglePublished = async (event: EventItem) => {
    try {
      await api.updateEvent(event.id, { is_published: !event.is_published });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось изменить статус");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">События посёлка</h1>
          <p className="text-muted-foreground mt-1">
            Опубликованные события автоматически появляются на главной в блоке «Ближайшие события».
          </p>
        </div>
        <Button onClick={() => { resetForm(); setShowForm(true); }}>
          {showForm && !editId ? "Отмена" : "+ Добавить событие"}
        </Button>
      </div>

      {msg && <p className="text-green-700">{msg}</p>}
      {error && <p className="text-destructive">{error}</p>}

      {showForm && (
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
              <label className="md:col-span-2 grid gap-1">
                <span className="text-sm font-medium">Название</span>
                <input
                  className="rounded-md border px-3 py-2"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  required
                />
              </label>
              <label className="md:col-span-2 grid gap-1">
                <span className="text-sm font-medium">Описание</span>
                <textarea
                  className="rounded-md border px-3 py-2 min-h-[80px]"
                  value={form.description || ""}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </label>
              <label className="grid gap-1">
                <span className="text-sm font-medium">Начало</span>
                <input
                  type="datetime-local"
                  className="rounded-md border px-3 py-2"
                  value={toLocalInputValue(form.starts_at)}
                  onChange={(e) => setForm({ ...form, starts_at: e.target.value })}
                  required
                />
              </label>
              <label className="grid gap-1">
                <span className="text-sm font-medium">Окончание</span>
                <input
                  type="datetime-local"
                  className="rounded-md border px-3 py-2"
                  value={toLocalInputValue(form.ends_at)}
                  onChange={(e) => setForm({ ...form, ends_at: e.target.value })}
                />
              </label>
              <label className="grid gap-1">
                <span className="text-sm font-medium">Место</span>
                <input
                  className="rounded-md border px-3 py-2"
                  value={form.location || ""}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                />
              </label>
              <label className="grid gap-1">
                <span className="text-sm font-medium">Категория</span>
                <select
                  className="rounded-md border px-3 py-2"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </label>
              <label className="md:col-span-2 grid gap-1">
                <span className="text-sm font-medium">Ссылка (необязательно)</span>
                <input
                  className="rounded-md border px-3 py-2"
                  value={form.source_url || ""}
                  onChange={(e) => setForm({ ...form, source_url: e.target.value })}
                  placeholder="https://..."
                />
              </label>
              <label className="flex items-center gap-2 md:col-span-2">
                <input
                  type="checkbox"
                  checked={form.is_published ?? true}
                  onChange={(e) => setForm({ ...form, is_published: e.target.checked })}
                />
                <span className="text-sm">Опубликовать на сайте</span>
              </label>
              <div className="md:col-span-2 flex gap-2">
                <Button type="submit">{editId ? "Сохранить" : "Создать"}</Button>
                <Button type="button" variant="outline" onClick={resetForm}>Отмена</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {items.map((event) => (
          <Card key={event.id}>
            <CardContent className="pt-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  {event.category_label} · {event.starts_at_label}
                  {!event.is_published && " · черновик"}
                </p>
                <p className="font-semibold text-lg">{event.title}</p>
                {event.location && <p className="text-sm text-muted-foreground">{event.location}</p>}
                {event.description && <p className="text-sm mt-1">{event.description}</p>}
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => startEdit(event)}>Изменить</Button>
                <Button size="sm" variant="outline" onClick={() => togglePublished(event)}>
                  {event.is_published ? "Снять" : "Опубликовать"}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {items.length === 0 && !error && (
          <p className="text-muted-foreground">Пока нет событий — добавьте первое.</p>
        )}
      </div>
    </div>
  );
}
