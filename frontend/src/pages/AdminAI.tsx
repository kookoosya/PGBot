import { FormEvent, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, AIEntitlementRow, AIProviderKeyRow } from "@/lib/api";

export function AdminAI() {
  const [items, setItems] = useState<AIEntitlementRow[]>([]);
  const [keys, setKeys] = useState<AIProviderKeyRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [keysLoading, setKeysLoading] = useState(true);
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
  const [keyForm, setKeyForm] = useState({ api_key: "", label: "", priority: "100" });

  const loadEntitlements = () => {
    setLoading(true);
    api
      .getAIEntitlements()
      .then((r) => setItems(r.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка загрузки"))
      .finally(() => setLoading(false));
  };

  const loadKeys = () => {
    setKeysLoading(true);
    api
      .getAIKeys()
      .then((r) => setKeys(r.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка ключей"))
      .finally(() => setKeysLoading(false));
  };

  useEffect(() => {
    loadEntitlements();
    loadKeys();
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
      loadEntitlements();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось выдать доступ");
    }
  };

  const submitKey = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      const res = await api.addAIKey({
        api_key: keyForm.api_key.trim(),
        label: keyForm.label.trim() || undefined,
        priority: keyForm.priority ? Number(keyForm.priority) : 100,
      });
      setSuccess(res.message);
      setKeyForm({ api_key: "", label: "", priority: "100" });
      loadKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось добавить ключ");
    }
  };

  const revoke = async (id: number) => {
    if (!window.confirm("Отключить доступ?")) return;
    try {
      await api.revokeAIEntitlement(id);
      loadEntitlements();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  };

  const toggleKey = async (row: AIProviderKeyRow) => {
    try {
      if (row.is_active) await api.deactivateAIKey(row.id);
      else await api.activateAIKey(row.id);
      loadKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка ключа");
    }
  };

  const removeKey = async (id: number) => {
    if (!window.confirm("Удалить ключ из пула?")) return;
    try {
      await api.deleteAIKey(id);
      loadKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка удаления");
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <PageHeader icon="🤖" title="ИИ — ключи и доступ" subtitle="Пул ключей для всех оплативших" />

      <div className="rounded-lg border bg-card p-4 text-sm space-y-2">
        <p className="m-0"><strong>Гость:</strong> 10 сообщений/день без входа.</p>
        <p className="m-0"><strong>Пробный:</strong> 10/день, 7 дней после входа (авто).</p>
        <p className="m-0"><strong>ИИ Pro:</strong> платная подписка после оплаты (лимит в .env: AI_PRO_DAILY_LIMIT).</p>
        <p className="m-0 text-muted-foreground">
          Лимиты: гость AI_FREE_DAILY_LIMIT, пробный AI_TRIAL_DAILY_LIMIT, Pro AI_PRO_DAILY_LIMIT — в .env на сервере.
          Ключи Gemini крутятся по очереди для всех активных подписок.
        </p>
      </div>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-lg font-semibold m-0">Пул ключей Gemini</h2>
        <p className="text-sm text-muted-foreground m-0">
          Добавляйте ключи, когда заканчивается лимит API. При ошибке запрос переключится на следующий ключ.
        </p>
        <form onSubmit={submitKey} className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm sm:col-span-2">
            Ключ Gemini
            <Input
              className="mt-1 font-mono text-xs"
              value={keyForm.api_key}
              onChange={(e) => setKeyForm((f) => ({ ...f, api_key: e.target.value }))}
              placeholder="AIza…"
              required
            />
          </label>
          <label className="text-sm">
            Подпись
            <Input
              className="mt-1"
              value={keyForm.label}
              onChange={(e) => setKeyForm((f) => ({ ...f, label: e.target.value }))}
              placeholder="Аккаунт 1"
            />
          </label>
          <label className="text-sm">
            Приоритет (меньше — раньше)
            <Input
              className="mt-1"
              value={keyForm.priority}
              onChange={(e) => setKeyForm((f) => ({ ...f, priority: e.target.value }))}
            />
          </label>
          <div className="sm:col-span-2">
            <Button type="submit">Добавить ключ</Button>
          </div>
        </form>

        {keysLoading ? (
          <p className="text-sm text-muted-foreground m-0">Загрузка ключей…</p>
        ) : keys.length === 0 ? (
          <p className="text-sm text-muted-foreground m-0">Ключей в базе нет — можно добавить выше или GEMINI_API_KEY в .env</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b text-left">
                  <th className="py-2 pr-2">ID</th>
                  <th className="py-2 pr-2">Ключ</th>
                  <th className="py-2 pr-2">Статус</th>
                  <th className="py-2 pr-2">Исп.</th>
                  <th className="py-2 pr-2">Ошиб.</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {keys.map((row) => (
                  <tr key={row.id} className="border-b">
                    <td className="py-2 pr-2">{row.id}</td>
                    <td className="py-2 pr-2">
                      <span className="font-mono">{row.masked_key}</span>
                      {row.label && <span className="text-muted-foreground"> · {row.label}</span>}
                    </td>
                    <td className="py-2 pr-2">{row.is_active ? "активен" : "выкл"}</td>
                    <td className="py-2 pr-2">{row.use_count}</td>
                    <td className="py-2 pr-2">{row.error_count}</td>
                    <td className="py-2 whitespace-nowrap">
                      <button type="button" className="text-forest hover:underline mr-2" onClick={() => toggleKey(row)}>
                        {row.is_active ? "Выкл" : "Вкл"}
                      </button>
                      <button type="button" className="text-red-600 hover:underline" onClick={() => removeKey(row.id)}>
                        Удалить
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <form onSubmit={submit} className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-lg font-semibold m-0">Выдать доступ после оплаты</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm">
            Тариф
            <select
              className="mt-1 w-full border rounded px-3 py-2"
              value={form.plan_id}
              onChange={(e) => setForm((f) => ({ ...f, plan_id: e.target.value }))}
            >
              <option value="pro">ИИ Pro</option>
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
        <Button type="submit">Активировать доступ</Button>
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
