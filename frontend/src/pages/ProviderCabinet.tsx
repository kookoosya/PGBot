import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

const DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export function ProviderCabinet() {
  const { user, loading, login, logout } = useAuth();
  const [profile, setProfile] = useState<Awaited<ReturnType<typeof api.getMyProviderProfile>> | null>(null);
  const [appointments, setAppointments] = useState<Awaited<ReturnType<typeof api.getMyAppointments>>>([]);
  const [busyBlocks, setBusyBlocks] = useState<Awaited<ReturnType<typeof api.getMyBusyBlocks>>>([]);
  const [schedule, setSchedule] = useState<{ day_of_week: number; start_time: string; end_time: string; is_working: boolean }[]>([]);
  const [busyForm, setBusyForm] = useState({ block_date: "", start_time: "12:00", end_time: "14:00", reason: "Занят" });
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [msg, setMsg] = useState("");
  const [tab, setTab] = useState<"schedule" | "busy" | "bookings">("schedule");

  const load = () => {
    api.getMyProviderProfile().then((p) => {
      setProfile(p);
      setSchedule(p.schedule.map((s) => ({
        day_of_week: s.day_of_week, start_time: s.start_time,
        end_time: s.end_time, is_working: s.is_working,
      })));
    }).catch(() => setProfile(null));
    api.getMyAppointments().then(setAppointments).catch(console.error);
    api.getMyBusyBlocks().then(setBusyBlocks).catch(console.error);
  };

  useEffect(() => {
    if (user?.role === "service_provider") load();
  }, [user]);

  if (loading) return <div className="p-8 text-center">Загрузка...</div>;

  if (!user) {
    return (
      <div className="mx-auto max-w-md px-4 py-16">
        <h2 className="text-2xl font-bold text-center mb-6">Кабинет мастера</h2>
        <form onSubmit={async (e) => { e.preventDefault(); await login(loginForm.username, loginForm.password); }} className="pushkin-card p-6 space-y-4">
          <Input placeholder="Логин" value={loginForm.username} onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })} />
          <Input type="password" placeholder="Пароль" value={loginForm.password} onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })} />
          <Button type="submit" className="w-full">Войти</Button>
          <Link to="/services/register" className="block text-center text-sm text-primary hover:underline">Нет аккаунта? Зарегистрироваться</Link>
        </form>
      </div>
    );
  }

  if (user.role !== "service_provider") {
    return <Navigate to="/services" replace />;
  }

  if (user && !profile) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center pushkin-card p-8 mt-12">
        <p className="text-lg">⏳ Профиль на проверке</p>
        <p className="text-muted-foreground mt-2">После одобрения администратором откроется кабинет.</p>
        <Button variant="outline" className="mt-4" onClick={logout}>Выйти</Button>
      </div>
    );
  }

  const saveSchedule = async () => {
    await api.updateMySchedule(schedule.filter((s) => s.is_working));
    setMsg("Расписание сохранено");
    load();
  };

  const addBusy = async () => {
    await api.addBusyBlock(busyForm);
    setMsg("Время отмечено как занятое");
    load();
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Кабинет: {profile?.full_name}</h2>
          <p className="text-sm text-muted-foreground">{profile?.phone} · {profile?.address}</p>
        </div>
        <Button variant="outline" size="sm" onClick={logout}>Выйти</Button>
      </div>

      {msg && <p className="text-sm text-green-700 mb-4">{msg}</p>}

      <div className="flex gap-2 border-b mb-6">
        {(["schedule", "busy", "bookings"] as const).map((t) => (
          <button key={t} className={`px-4 py-2 text-sm ${tab === t ? "border-b-2 border-amber-500 font-medium" : "text-muted-foreground"}`} onClick={() => setTab(t)}>
            {t === "schedule" ? "📅 Расписание" : t === "busy" ? "🔴 Занят" : "📋 Записи"}
          </button>
        ))}
      </div>

      {tab === "schedule" && (
        <div className="pushkin-card p-6 space-y-3">
          <p className="text-sm text-muted-foreground">Укажите, когда вы принимаете клиентов</p>
          {DAYS.map((day, i) => {
            const s = schedule.find((x) => x.day_of_week === i) || { day_of_week: i, start_time: "09:00", end_time: "18:00", is_working: i < 6 };
            return (
              <div key={i} className="flex items-center gap-2 text-sm">
                <label className="w-10 flex items-center gap-1">
                  <input type="checkbox" checked={s.is_working} onChange={(e) => {
                    const next = schedule.filter((x) => x.day_of_week !== i);
                    next.push({ ...s, is_working: e.target.checked });
                    setSchedule(next.sort((a, b) => a.day_of_week - b.day_of_week));
                  }} />
                  {day}
                </label>
                {s.is_working && (
                  <>
                    <input className="border rounded px-2 py-1 w-20" value={s.start_time} onChange={(e) => {
                      const next = schedule.filter((x) => x.day_of_week !== i);
                      next.push({ ...s, start_time: e.target.value });
                      setSchedule(next);
                    }} />
                    <span>—</span>
                    <input className="border rounded px-2 py-1 w-20" value={s.end_time} onChange={(e) => {
                      const next = schedule.filter((x) => x.day_of_week !== i);
                      next.push({ ...s, end_time: e.target.value });
                      setSchedule(next);
                    }} />
                  </>
                )}
              </div>
            );
          })}
          <Button onClick={saveSchedule} className="w-full mt-4">Сохранить расписание</Button>
        </div>
      )}

      {tab === "busy" && (
        <div className="space-y-4">
          <div className="pushkin-card p-6 space-y-3">
            <p className="text-sm font-medium">Отметить занятое время</p>
            <input type="date" className="w-full border rounded px-3 py-2 text-sm" value={busyForm.block_date} onChange={(e) => setBusyForm({ ...busyForm, block_date: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className="border rounded px-3 py-2 text-sm" value={busyForm.start_time} onChange={(e) => setBusyForm({ ...busyForm, start_time: e.target.value })} />
              <input className="border rounded px-3 py-2 text-sm" value={busyForm.end_time} onChange={(e) => setBusyForm({ ...busyForm, end_time: e.target.value })} />
            </div>
            <Input placeholder="Причина (обед, выезд...)" value={busyForm.reason} onChange={(e) => setBusyForm({ ...busyForm, reason: e.target.value })} />
            <Button onClick={addBusy} className="w-full">Отметить занятым</Button>
          </div>
          {busyBlocks.map((b) => (
            <div key={b.id} className="pushkin-card p-4 flex justify-between text-sm">
              <span>{b.block_date} · {b.start_time}–{b.end_time} {b.reason && `(${b.reason})`}</span>
              <button className="text-red-600" onClick={() => api.deleteBusyBlock(b.id).then(load)}>✕</button>
            </div>
          ))}
        </div>
      )}

      {tab === "bookings" && (
        <div className="space-y-3">
          {appointments.length === 0 && <p className="text-muted-foreground text-center py-8">Записей пока нет</p>}
          {appointments.map((a) => (
            <div key={a.id} className="pushkin-card p-4 text-sm">
              <p className="font-medium">{a.appointment_date} · {a.start_time}–{a.end_time}</p>
              <p>{a.service_name} — {a.client_name}</p>
              <p className="text-muted-foreground">Статус: {a.status}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
