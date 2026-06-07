import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

export function RegisterOrganization() {
  const [form, setForm] = useState({
    organization_name: "",
    responsible_full_name: "",
    responsible_position: "",
    org_address: "",
    phone: "",
    email: "",
    inn: "",
    website: "",
    description: "",
    username: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.registerOrganization(form);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="page-section max-w-lg mx-auto text-center pushkin-card p-10">
        <span className="text-5xl">✅</span>
        <h2 className="text-2xl font-bold mt-4">Заявка принята</h2>
        <p className="text-muted-foreground mt-4">
          Мы проверим организацию и ответственное лицо. После одобрения вы сможете войти в личный кабинет
          и управлять информацией о своём бизнесе на портале.
        </p>
        <Link to="/" className="inline-block mt-6 text-primary hover:underline">На главную</Link>
      </div>
    );
  }

  return (
    <div className="page-section max-w-xl mx-auto">
      <h1 className="text-2xl font-bold text-center mb-2">Регистрация организации</h1>
      <div className="human-note mb-8">
        <p className="m-0 text-sm">
          <strong>Почему полная форма?</strong> На портале посёлка публикуются магазины, аптеки и услуги.
          Нам важно знать <strong>ответственное лицо</strong> — того, кто отвечает за информацию и
          связь с жителями. Это защищает и вас, и посетителей сайта.
        </p>
      </div>

      <form onSubmit={submit} className="pushkin-card p-6 space-y-4">
        <h3 className="font-semibold">Организация</h3>
        <Input placeholder="Название (ИП Иванов / ООО ...)" value={form.organization_name} onChange={(e) => set("organization_name", e.target.value)} required />
        <Input placeholder="Адрес в посёлке" value={form.org_address} onChange={(e) => set("org_address", e.target.value)} required />
        <Input placeholder="ИНН (необязательно)" value={form.inn} onChange={(e) => set("inn", e.target.value)} />
        <Input placeholder="Сайт (необязательно)" value={form.website} onChange={(e) => set("website", e.target.value)} />
        <textarea
          className="w-full border rounded px-3 py-2 text-sm min-h-[80px]"
          placeholder="Чем занимается организация? (мин. 20 символов)"
          value={form.description}
          onChange={(e) => set("description", e.target.value)}
          required
          minLength={20}
        />

        <h3 className="font-semibold pt-2">Ответственное лицо</h3>
        <Input placeholder="ФИО полностью" value={form.responsible_full_name} onChange={(e) => set("responsible_full_name", e.target.value)} required />
        <Input placeholder="Должность (директор, управляющий...)" value={form.responsible_position} onChange={(e) => set("responsible_position", e.target.value)} required />
        <Input placeholder="Телефон" value={form.phone} onChange={(e) => set("phone", e.target.value)} required />
        <Input type="email" placeholder="Email" value={form.email} onChange={(e) => set("email", e.target.value)} required />

        <h3 className="font-semibold pt-2">Вход в кабинет</h3>
        <Input placeholder="Логин" value={form.username} onChange={(e) => set("username", e.target.value)} required />
        <Input type="password" placeholder="Пароль" value={form.password} onChange={(e) => set("password", e.target.value)} required minLength={10} />

        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Отправка..." : "Подать на проверку"}
        </Button>
      </form>

      <p className="text-center text-sm mt-6 text-muted-foreground">
        <Link to="/register" className="hover:underline">← Все варианты</Link>
      </p>
    </div>
  );
}
