import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

const DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export function ServiceRegister() {
  const [types, setTypes] = useState<{ value: string; label: string }[]>([]);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    full_name: "", phone: "", email: "", username: "", password: "",
    bio: "", address: "",
    service_type: "manicure", service_name: "", service_duration: 60, service_price: "",
    schedule: DAYS.map((_, i) => ({
      day_of_week: i, start_time: i < 5 ? "09:00" : i === 5 ? "10:00" : "09:00",
      end_time: i < 5 ? "18:00" : i === 5 ? "16:00" : "18:00",
      is_working: i < 6,
    })),
  });

  useEffect(() => { api.getServiceTypes().then(setTypes).catch(console.error); }, []);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.registerProvider({
        full_name: form.full_name,
        phone: form.phone,
        email: form.email || undefined,
        username: form.username,
        password: form.password,
        bio: form.bio,
        address: form.address,
        services: [{
          service_type: form.service_type,
          name: form.service_name,
          duration_minutes: form.service_duration,
          price: form.service_price ? +form.service_price : undefined,
        }],
        schedule: form.schedule.filter((s) => s.is_working).map((s) => ({
          day_of_week: s.day_of_week,
          start_time: s.start_time,
          end_time: s.end_time,
          is_working: true,
        })),
      });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  };

  if (success) {
    return (
      <div className="mx-auto max-w-lg px-6 py-16 text-center pushkin-card p-10 mt-12">
        <span className="text-5xl">✅</span>
        <h2 className="text-2xl font-bold mt-4">Заявка отправлена!</h2>
        <p className="text-muted-foreground mt-4">После проверки вы появитесь в каталоге мастеров.</p>
        <div className="flex flex-wrap gap-4 justify-center mt-6">
          <Link to="/cabinet/login?next=/services/cabinet" className="text-primary hover:underline font-medium">
            Войти после одобрения →
          </Link>
          <Link to="/services" className="text-muted-foreground hover:underline">К услугам</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-6 py-12">
      <h2 className="text-3xl font-bold text-center mb-2">Регистрация мастера</h2>
      <p className="text-center text-muted-foreground mb-2">Маникюр, стрижки, брови и другие услуги</p>
      <p className="text-center text-sm mb-8">
        <Link to="/register" className="text-primary hover:underline">← Все варианты регистрации</Link>
      </p>
      <Card className="pushkin-card">
        <CardHeader><CardTitle>Ваши данные</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <Input placeholder="ФИО" value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required />
            <Input placeholder="Телефон" value={form.phone} onChange={(e) => set("phone", e.target.value)} required />
            <Input placeholder="Адрес приёма" value={form.address} onChange={(e) => set("address", e.target.value)} />
            <textarea className="w-full border rounded px-3 py-2 text-sm min-h-[60px]" placeholder="О себе" value={form.bio} onChange={(e) => set("bio", e.target.value)} />
            <div className="grid grid-cols-2 gap-2">
              <Input placeholder="Логин" value={form.username} onChange={(e) => set("username", e.target.value)} required />
              <Input type="password" placeholder="Пароль" value={form.password} onChange={(e) => set("password", e.target.value)} required />
            </div>
            <Input type="email" placeholder="Email" value={form.email} onChange={(e) => set("email", e.target.value)} />
            <hr />
            <p className="font-medium text-sm">Услуга</p>
            <select className="w-full border rounded px-3 py-2 text-sm" value={form.service_type} onChange={(e) => set("service_type", e.target.value)}>
              {types.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
            <Input placeholder="Название (напр. Классический маникюр)" value={form.service_name} onChange={(e) => set("service_name", e.target.value)} required />
            <div className="grid grid-cols-2 gap-2">
              <Input type="number" placeholder="Минут" value={form.service_duration} onChange={(e) => set("service_duration", e.target.value)} />
              <Input type="number" placeholder="Цена ₽" value={form.service_price} onChange={(e) => set("service_price", e.target.value)} />
            </div>
            <hr />
            <p className="font-medium text-sm">Расписание</p>
            {form.schedule.map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <label className="w-8 flex items-center gap-1">
                  <input type="checkbox" checked={s.is_working} onChange={(e) => {
                    const sch = [...form.schedule];
                    sch[i] = { ...sch[i], is_working: e.target.checked };
                    setForm({ ...form, schedule: sch });
                  }} />
                  {DAYS[i]}
                </label>
                {s.is_working && (
                  <>
                    <input className="border rounded px-2 py-1 w-20" value={s.start_time} onChange={(e) => {
                      const sch = [...form.schedule]; sch[i].start_time = e.target.value; setForm({ ...form, schedule: sch });
                    }} />
                    <span>—</span>
                    <input className="border rounded px-2 py-1 w-20" value={s.end_time} onChange={(e) => {
                      const sch = [...form.schedule]; sch[i].end_time = e.target.value; setForm({ ...form, schedule: sch });
                    }} />
                  </>
                )}
              </div>
            ))}
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full">Подать заявку</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
