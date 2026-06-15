import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState, LiteraryInlineLoader } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";
import { useUserAuth } from "@/lib/userAuth";
import { api } from "@/lib/api";

const DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
const copy = PAGE_SECTIONS.provider;

export function ProviderCabinet() {
  const { user, loading, logout } = useUserAuth();
  const [profile, setProfile] = useState<Awaited<ReturnType<typeof api.getMyProviderProfile>> | null>(null);
  const [appointments, setAppointments] = useState<Awaited<ReturnType<typeof api.getMyAppointments>>>([]);
  const [busyBlocks, setBusyBlocks] = useState<Awaited<ReturnType<typeof api.getMyBusyBlocks>>>([]);
  const [schedule, setSchedule] = useState<{ day_of_week: number; start_time: string; end_time: string; is_working: boolean }[]>([]);
  const [busyForm, setBusyForm] = useState({ block_date: "", start_time: "12:00", end_time: "14:00", reason: "Занят" });
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

  if (loading) {
    return <LiteraryInlineLoader label="Загрузка кабинета…" />;
  }

  if (!user) {
    return <Navigate to="/cabinet/login?next=/services/cabinet" replace />;
  }

  if (user.role !== "service_provider") {
    return <Navigate to="/cabinet" replace />;
  }

  if (user && !profile) {
    return (
      <div className="literary-page page-section max-w-lg mx-auto py-12">
        <LiteraryEmptyState
          icon="⏳"
          title="Профиль на проверке"
          text="После одобрения администратором откроется кабинет мастера с расписанием и записями."
        >
          <button type="button" className="literary-btn literary-btn--ghost mt-3" onClick={logout}>
            Выйти
          </button>
        </LiteraryEmptyState>
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
    <div className="literary-page page-section max-w-3xl mx-auto">
      <PageHeader icon="💇" title={`${copy.title}: ${profile?.full_name}`} subtitle={copy.lead}>
        <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={logout}>Выйти</button>
      </PageHeader>
      <p className="text-sm text-muted-foreground -mt-4 mb-6">
        {profile?.phone}{profile?.address ? ` · ${profile.address}` : ""}
      </p>

      {msg && <p className="text-sm text-green-800 mb-4 literary-page-note p-3">{msg}</p>}

      <div className="literary-provider-tabs" role="tablist">
        {(["schedule", "busy", "bookings"] as const).map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            className={`filter-chip${tab === t ? " filter-chip-active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t === "schedule" ? "📅 Расписание" : t === "busy" ? "🔴 Занят" : "📋 Записи"}
          </button>
        ))}
      </div>

      {tab === "schedule" && (
        <div className="page-panel page-panel--forest literary-auth-panel space-y-3">
          <p className="text-sm text-muted-foreground m-0">Укажите, когда вы принимаете клиентов</p>
          {DAYS.map((day, i) => {
            const s = schedule.find((x) => x.day_of_week === i) || { day_of_week: i, start_time: "09:00", end_time: "18:00", is_working: i < 6 };
            return (
              <div key={i} className="flex items-center gap-2 text-sm flex-wrap">
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
                    <input className="border rounded px-2 py-1 w-20 pushkin-select" value={s.start_time} onChange={(e) => {
                      const next = schedule.filter((x) => x.day_of_week !== i);
                      next.push({ ...s, start_time: e.target.value });
                      setSchedule(next);
                    }} />
                    <span>—</span>
                    <input className="border rounded px-2 py-1 w-20 pushkin-select" value={s.end_time} onChange={(e) => {
                      const next = schedule.filter((x) => x.day_of_week !== i);
                      next.push({ ...s, end_time: e.target.value });
                      setSchedule(next);
                    }} />
                  </>
                )}
              </div>
            );
          })}
          <button type="button" className="literary-btn literary-btn--primary w-full mt-4" onClick={saveSchedule}>
            Сохранить расписание
          </button>
        </div>
      )}

      {tab === "busy" && (
        <div className="space-y-4">
          <div className="page-panel page-panel--gold literary-auth-panel space-y-3">
            <p className="text-sm font-medium m-0">Отметить занятое время</p>
            <input type="date" className="w-full border rounded px-3 py-2 text-sm pushkin-select" value={busyForm.block_date} onChange={(e) => setBusyForm({ ...busyForm, block_date: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className="border rounded px-3 py-2 text-sm pushkin-select" value={busyForm.start_time} onChange={(e) => setBusyForm({ ...busyForm, start_time: e.target.value })} />
              <input className="border rounded px-3 py-2 text-sm pushkin-select" value={busyForm.end_time} onChange={(e) => setBusyForm({ ...busyForm, end_time: e.target.value })} />
            </div>
            <Input placeholder="Причина (обед, выезд…)" value={busyForm.reason} onChange={(e) => setBusyForm({ ...busyForm, reason: e.target.value })} className="pushkin-select" />
            <button type="button" className="literary-btn literary-btn--primary w-full" onClick={addBusy}>Отметить занятым</button>
          </div>
          {busyBlocks.map((b) => (
            <div key={b.id} className="literary-card literary-card--gold p-4 flex justify-between text-sm gap-2">
              <span>{b.block_date} · {b.start_time}–{b.end_time} {b.reason && `(${b.reason})`}</span>
              <button type="button" className="text-red-700 shrink-0" onClick={() => api.deleteBusyBlock(b.id).then(load)}>✕</button>
            </div>
          ))}
        </div>
      )}

      {tab === "bookings" && (
        <div className="space-y-3">
          {appointments.length === 0 && (
            <p className="text-muted-foreground text-center py-8 literary-page-note">Записей пока нет</p>
          )}
          {appointments.map((a) => (
            <div key={a.id} className="literary-card literary-card--forest p-4 text-sm">
              <p className="font-medium m-0">{a.appointment_date} · {a.start_time}–{a.end_time}</p>
              <p className="mt-1 mb-0">{a.service_name} — {a.client_name}</p>
              <p className="text-muted-foreground m-0 mt-1">Статус: {a.status}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
