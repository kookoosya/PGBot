import { FormEvent, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, AIEntitlementRow } from "@/lib/api";

export function AdminAI() {
  const [items, setItems] = useState<AIEntitlementRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState({
    plan_id: "pro",
    user_id: "",
    vk_id: "",
    payment_reference: "",
    payment_amount: "",
    notes: "",
  });

  const load = () => {
    setLoading(true);
    api
      .getAIEntitlements()
      .then((r) => setItems(r.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка загрузки"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      const res = await api.grantAIEntitlement({
        plan_id: form.plan_id,
        user_id: form.user_id ? Number(form.user_id) : undefined,
        vk_id: form.vk_id ? Number(form.vk_id) : undefined,
        payment_reference: form.payment_reference || undefined,
        payment_amount: form.payment_amount ? Number(form.payment_amount) : undefined,
        notes: form.notes || undefined,
      });
      setSuccess(res.message);
      setForm({ plan_id: "pro", user_id: "", vk_id: "", payment_reference: "", payment_amount: "", notes: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось выдать доступ");
    }
  };

  const revoke = async (id: number) => {
    if (!window.confirm("Отключить доступ?")) return;
    try {
      await api.revokeAIEntitlement(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <PageHeader icon="🤖" title="ИИ — доступ Pro" subtitle="Пробный период и оплата переводом" />

      <div className="rounded-lg border bg-card p-4 text-sm space-y-2">
        <p className="m-0"><strong>Бесплатно:</strong> 10 сообщений/день.</p>
        <p className="m-0"><strong>Пробный:</strong> 7 дней после первого входа, 25 сообщений/день (авто).</p>
        <p className="m-0"><strong>ИИ Pro:</strong> до 50 сообщений/день, режимы учёба/код.</p>
        <p className="m-0"><strong>ИИ Pro+:</strong> до 100 сообщений/день.</p>
        <p className="m-0 text-muted-foreground">
          Ключ Gemini — в .env (GEMINI_API_KEY). Лимит умных ответов Gemini — 50/сутки на аккаунт.
        </p>
      </div>

      <form onSubmit={submit} className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-lg font-semibold m-0">Выдать доступ</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm">
            Тариф
            <select
              className="mt-1 w-full border rounded px-3 py-2"
              value={form.plan_id}
              onChange={(e) => setForm((f) => ({ ...f, plan_id: e.target.value }))}
            >
              <option value="pro">ИИ Pro</option>
              <option value="pro_plus">ИИ Pro+</option>
            </select>
          </label>
          <label className="text-sm">
            ID пользователя (users.id)
            <Input
              className="mt-1"
              value={form.user_id}
              onChange={(e) => setForm((f) => ({ ...f, user_id: e.target.value }))}
              placeholder="например 5"
            />
          </label>
          <label className="text-sm">
            VK ID (опционально)
            <Input
              className="mt-1"
              value={form.vk_id}
              onChange={(e) => setForm((f) => ({ ...f, vk_id: e.target.value }))}
            />
          </label>
          <label className="text-sm">
            Сумма ₽
            <Input
              className="mt-1"
              value={form.payment_amount}
              onChange={(e) => setForm((f) => ({ ...f, payment_amount: e.target.value }))}
            />
          </label>
          <label className="text-sm sm:col-span-2">
            Комментарий к переводу
            <Input
              className="mt-1"
              value={form.payment_reference}
              onChange={(e) => setForm((f) => ({ ...f, payment_reference: e.target.value }))}
              placeholder="ИИ Pro · username"
            />
          </label>
          <label className="text-sm sm:col-span-2">
            Заметка
            <Input
              className="mt-1"
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            />
          </label>
        </div>
        {error && <p className="text-sm text-red-600 m-0">{error}</p>}
        {success && <p className="text-sm text-green-700 m-0">{success}</p>}
        <Button type="submit">Активировать Pro</Button>
      </form>

      <section>
        <h2 className="text-lg font-semibold mb-3">Выданные доступы</h2>
        {loading ? (
          <p className="text-sm text-muted-foreground">Загрузка…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground">Пока нет записей</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b text-left">
                  <th className="py-2 pr-2">ID</th>
                  <th className="py-2 pr-2">User</th>
                  <th className="py-2 pr-2">План</th>
                  <th className="py-2 pr-2">До</th>
                  <th className="py-2 pr-2">Статус</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.id} className="border-b">
                    <td className="py-2 pr-2">{row.id}</td>
                    <td className="py-2 pr-2">{row.user_id ?? row.vk_id ?? row.web_identifier ?? "—"}</td>
                    <td className="py-2 pr-2">{row.plan_id}</td>
                    <td className="py-2 pr-2">
                      {row.expires_at ? new Date(row.expires_at).toLocaleDateString("ru-RU") : "∞"}
                    </td>
                    <td className="py-2 pr-2">{row.is_active ? "активен" : "выкл"}</td>
                    <td className="py-2">
                      {row.is_active && (
                        <button type="button" className="text-red-600 hover:underline" onClick={() => revoke(row.id)}>
                          Отключить
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
