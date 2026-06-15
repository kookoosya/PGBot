import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LITERARY_VERSES } from "@/lib/literaryCopy";
import { Badge } from "@/components/ui/badge";
import { api, Issue } from "@/lib/api";
import { isOfficialUser, useUserAuth } from "@/lib/userAuth";
import { formatDate, STATUS_COLORS, STATUS_LABELS } from "@/lib/utils";

const STATUS_LABELS_VERIFY: Record<string, { text: string; tone: string }> = {
  pending: { text: "На проверке — мы свяжемся с вами", tone: "text-amber-700 bg-amber-50 border-amber-200" },
  approved: { text: "Подтверждено", tone: "text-green-700 bg-green-50 border-green-200" },
  rejected: { text: "Заявка отклонена — напишите нам", tone: "text-red-700 bg-red-50 border-red-200" },
};

export function UserCabinet() {
  const { user, loading, logout } = useUserAuth();
  const [recentIssues, setRecentIssues] = useState<Issue[]>([]);

  useEffect(() => {
    if (!user || isOfficialUser(user)) return;
    api.getMyIssues({ limit: "5" })
      .then((r) => setRecentIssues(r.items))
      .catch(() => setRecentIssues([]));
  }, [user]);

  if (loading) {
    return <div className="page-section text-center text-muted-foreground">Загрузка кабинета…</div>;
  }

  if (!user) return <Navigate to="/cabinet/login" replace />;
  if (isOfficialUser(user)) return <Navigate to="/official" replace />;
  if (user.role === "service_provider") return <Navigate to="/services/cabinet" replace />;

  const status = user.verification_status ? STATUS_LABELS_VERIFY[user.verification_status] : null;
  const isOrg = !!user.organization;

  return (
    <div className="page-section max-w-2xl mx-auto">
      <PageHeader
        icon="🪶"
        title={isOrg ? "Кабинет организации" : "Личный кабинет"}
        subtitle={`Добро пожаловать, ${user.full_name || user.username} — ваш уголок в Пушкиногорье`}
      >
        <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={logout}>Выйти</button>
      </PageHeader>

      <div className="literary-card literary-card--forest p-6 space-y-4 mb-6">
        <h2 className="literary-title text-lg m-0">Профиль</h2>
        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Логин</dt>
            <dd className="font-medium">{user.username}</dd>
          </div>
          {user.email && (
            <div>
              <dt className="text-muted-foreground">Email</dt>
              <dd className="font-medium">{user.email}</dd>
            </div>
          )}
          {user.phone && (
            <div>
              <dt className="text-muted-foreground">Телефон</dt>
              <dd className="font-medium">{user.phone}</dd>
            </div>
          )}
          {user.organization && (
            <div className="sm:col-span-2">
              <dt className="text-muted-foreground">Организация</dt>
              <dd className="font-medium">
                {user.organization}
                {user.position && <span className="text-muted-foreground"> · {user.position}</span>}
              </dd>
            </div>
          )}
        </dl>

        {status && (
          <p className={`text-sm px-3 py-2 rounded-lg border ${status.tone}`}>
            {status.text}
          </p>
        )}
      </div>

      {recentIssues.length > 0 && (
        <div className="literary-card literary-card--gold p-6 mb-6 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="literary-title text-lg m-0">Мои обращения</h2>
            <Link to="/complaints" className="literary-link text-sm">Все →</Link>
          </div>
          {recentIssues.map((issue) => (
            <div key={issue.id} className="border-t border-border pt-3 first:border-0 first:pt-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-sm">#{issue.id}</span>
                <Badge className={STATUS_COLORS[issue.status]}>{STATUS_LABELS[issue.status]}</Badge>
                <span className="text-xs text-muted-foreground ml-auto">{formatDate(issue.created_at)}</span>
              </div>
              <p className="text-sm mt-1 line-clamp-2">{issue.ai_analysis?.summary || issue.description}</p>
            </div>
          ))}
        </div>
      )}

      <div className="literary-cabinet-nav">
        <Link to="/classifieds" className="literary-useful-card literary-useful-card--gold no-underline text-inherit">
          <span className="literary-useful-icon">📋</span>
          <div>
            <h3 className="literary-useful-title">Объявления</h3>
            <p className="literary-useful-desc">Подать объявление соседям</p>
          </div>
        </Link>
        <Link to="/complaints" className="literary-useful-card no-underline text-inherit">
          <span className="literary-useful-icon">⚠️</span>
          <div>
            <h3 className="literary-useful-title">Обращения</h3>
            <p className="literary-useful-desc">Жалобы и статус рассмотрения</p>
          </div>
        </Link>
        <Link to="/events" className="literary-useful-card literary-useful-card--gold no-underline text-inherit">
          <span className="literary-useful-icon">📅</span>
          <div>
            <h3 className="literary-useful-title">Афиша</h3>
            <p className="literary-useful-desc">События в Пушкиногорье и Пскове</p>
          </div>
        </Link>
        <Link to="/map" className="literary-useful-card no-underline text-inherit">
          <span className="literary-useful-icon">🗺</span>
          <div>
            <h3 className="literary-useful-title">Карта</h3>
            <p className="literary-useful-desc">Заведения, отзывы, такси</p>
          </div>
        </Link>
      </div>

      <p className="text-center text-sm text-muted-foreground mt-8 italic">{LITERARY_VERSES.cabinet}</p>
    </div>
  );
}
