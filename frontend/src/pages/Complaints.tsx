import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { VkBotLink } from "@/components/VkBotLink";
import { api, Issue } from "@/lib/api";
import { useUserAuth } from "@/lib/userAuth";
import { formatDate, STATUS_COLORS, STATUS_LABELS } from "@/lib/utils";

export function Complaints() {
  const { user } = useUserAuth();
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [myIssues, setMyIssues] = useState<Issue[]>([]);
  const [showForm, setShowForm] = useState(true);
  const [form, setForm] = useState({
    description: "",
    address: "",
    category: "",
    full_name: "",
    phone: "",
  });
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    if (!user) {
      setMyIssues([]);
      return;
    }
    api.getIssues({ page_size: "10" })
      .then((r) => setMyIssues(r.items))
      .catch(() => setMyIssues([]));
  }, [user]);

  useEffect(() => {
    if (user) {
      setForm((f) => ({
        ...f,
        full_name: user.full_name || f.full_name,
        phone: user.phone || f.phone,
      }));
    }
  }, [user]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    try {
      const issue = await api.createIssue({
        description: form.description,
        address: form.address || undefined,
        category: form.category || undefined,
        full_name: user ? undefined : form.full_name,
        phone: user ? undefined : form.phone,
      });
      setMsgType("ok");
      setMsg(`Обращение #${issue.id} принято! Статус: на рассмотрении.`);
      setForm((f) => ({ ...f, description: "", address: "" }));
      if (user) {
        const r = await api.getIssues({ page_size: "10" });
        setMyIssues(r.items);
      }
    } catch (err) {
      setMsgType("err");
      setMsg(err instanceof Error ? err.message : "Ошибка отправки");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-section">
      <PageHeader
        icon="⚠️"
        title="Жалобы и обращения"
        subtitle="Сообщите о проблеме в посёлке — дороги, ЖКХ, освещение, мусор. Обращение увидят администрация и ответственные службы."
      />

      <div className="grid gap-8 lg:grid-cols-2 max-w-5xl mx-auto">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Подать обращение</h2>
            <Button variant="outline" size="sm" onClick={() => setShowForm(!showForm)}>
              {showForm ? "Свернуть" : "Открыть форму"}
            </Button>
          </div>

          {showForm && (
            <form onSubmit={submit} className="pushkin-card p-6 space-y-4">
              {!user && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="text-sm font-medium">Ваше имя</label>
                    <Input
                      value={form.full_name}
                      onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Телефон</label>
                    <Input
                      value={form.phone}
                      onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                      placeholder="+7..."
                      required
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="text-sm font-medium">Категория</label>
                <select
                  className="w-full h-10 rounded-md border px-3 text-sm bg-background"
                  value={form.category}
                  onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                >
                  <option value="">Авто (ИИ определит)</option>
                  {categories.map((c) => (
                    <option key={c.value} value={c.label}>{c.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium">Адрес / место</label>
                <Input
                  value={form.address}
                  onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                  placeholder="ул. Ленина, 5"
                />
              </div>

              <div>
                <label className="text-sm font-medium">Опишите проблему</label>
                <textarea
                  className="w-full rounded-md border px-3 py-2 text-sm bg-background min-h-[120px]"
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  placeholder="Например: не работает уличное освещение на перекрёстке..."
                  required
                  minLength={5}
                />
              </div>

              {msg && (
                <p className={`text-sm ${msgType === "ok" ? "text-green-700" : "text-destructive"}`}>
                  {msg}
                </p>
              )}

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Отправляем..." : "Отправить обращение"}
              </Button>

              {!user && (
                <p className="text-xs text-muted-foreground text-center">
                  <Link to="/cabinet/login" className="text-primary hover:underline">Войдите</Link>
                  {" "}чтобы видеть историю обращений
                </p>
              )}
            </form>
          )}
        </div>

        <div className="space-y-6">
          <div className="pushkin-card p-6">
            <h3 className="font-bold text-lg mb-3">🏛 Для служб и организаций</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Администрация, ЖКХ и организации регистрируются на портале и после проверки
              получают доступ к обращениям жителей.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link to="/register">
                <Button size="sm">Регистрация</Button>
              </Link>
              <Link to="/cabinet/login?next=/official">
                <Button size="sm" variant="outline">Вход для служб</Button>
              </Link>
            </div>
          </div>

          {user && (
            <div>
              <h3 className="font-bold text-lg mb-3">Мои обращения</h3>
              {myIssues.length === 0 ? (
                <p className="text-sm text-muted-foreground">Пока нет обращений</p>
              ) : (
                <div className="space-y-3">
                  {myIssues.map((issue) => (
                    <div key={issue.id} className="pushkin-card p-4">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold">#{issue.id}</span>
                        <Badge className={STATUS_COLORS[issue.status]}>
                          {STATUS_LABELS[issue.status]}
                        </Badge>
                        {issue.category && (
                          <Badge className="bg-gray-100 text-gray-700">{issue.category}</Badge>
                        )}
                      </div>
                      <p className="text-sm mt-2">
                        {issue.ai_analysis?.summary || issue.description}
                      </p>
                      {issue.resolution_text && (
                        <div className="mt-3 rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm">
                          <strong className="text-emerald-800">Ответ службы:</strong>
                          <p className="m-0 mt-1 text-emerald-900">{issue.resolution_text}</p>
                        </div>
                      )}
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatDate(issue.created_at)}
                        {issue.resolved_at && ` · решено ${formatDate(issue.resolved_at)}`}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="pushkin-card p-6 bg-muted/30">
            <h3 className="font-bold mb-2">💬 Через VK-бота</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Напишите боту — кнопка «Жалобы» или просто опишите проблему. Можно приложить фото.
            </p>
            <VkBotLink />
          </div>
        </div>
      </div>
    </div>
  );
}
