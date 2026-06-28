import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { CabinetSectionSkeleton, LiteraryEmptyState, LiteraryInlineLoader, LiteraryIssueCard } from "@/components/literary";
import { VkBotBanner } from "@/components/VkBotLink";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { api } from "@/lib/api/index";
import type { ClassifiedMineAd } from "@/lib/api/types/classifieds";
import type { Issue } from "@/lib/api/types/issues";
import { isOfficialUser, useUserAuth } from "@/lib/userAuth";
import { ISSUE_ACTIVE_STATUSES } from "@/lib/utils";

const STATUS_LABELS_VERIFY: Record<string, { text: string; tone: string }> = {
  pending: { text: "На проверке — мы свяжемся с вами", tone: "text-amber-700 bg-amber-50 border-amber-200" },
  approved: { text: "Подтверждено", tone: "text-green-700 bg-green-50 border-green-200" },
  rejected: { text: "Заявка отклонена — напишите нам", tone: "text-red-700 bg-red-50 border-red-200" },
};

const CLASSIFIED_STATUS: Record<string, string> = {
  pending: "На модерации",
  approved: "Опубликовано",
  rejected: "Отклонено",
};

function classifiedStatusLabel(ad: ClassifiedMineAd): string {
  if (ad.payment_status === "approved" && ad.is_active) return "Опубликовано";
  if (ad.payment_status === "rejected") return "Отклонено";
  return CLASSIFIED_STATUS[ad.payment_status] || ad.payment_status;
}

export function UserCabinet() {
  const { user, loading, logout } = useUserAuth();
  const [recentIssues, setRecentIssues] = useState<Issue[]>([]);
  const [myAds, setMyAds] = useState<ClassifiedMineAd[]>([]);
  const [issuesLoaded, setIssuesLoaded] = useState(false);
  const [adsLoaded, setAdsLoaded] = useState(false);

  useEffect(() => {
    if (!user || isOfficialUser(user)) {
      setIssuesLoaded(true);
      setAdsLoaded(true);
      return;
    }
    api.getMyIssues({ limit: "5" })
      .then((r) => setRecentIssues(r.items))
      .catch(() => setRecentIssues([]))
      .finally(() => setIssuesLoaded(true));

    api.getMyClassifieds({ page_size: "5" })
      .then((r) => setMyAds(r.items))
      .catch(() => setMyAds([]))
      .finally(() => setAdsLoaded(true));
  }, [user]);

  if (loading) {
    return <LiteraryInlineLoader label="Загрузка кабинета…" />;
  }

  if (!user) return <Navigate to="/cabinet/login" replace />;
  if (isOfficialUser(user)) return <Navigate to="/official" replace />;
  if (user.role === "service_provider") return <Navigate to="/services/cabinet" replace />;

  const status = user.verification_status ? STATUS_LABELS_VERIFY[user.verification_status] : null;
  const isOrg = !!user.organization;
  const activeIssues = recentIssues.filter((i) => ISSUE_ACTIVE_STATUSES.has(i.status)).length;
  const bothEmpty = issuesLoaded && recentIssues.length === 0 && adsLoaded && myAds.length === 0;
  const showIssuesEmpty = issuesLoaded && recentIssues.length === 0 && !bothEmpty;
  const showAdsEmpty = adsLoaded && myAds.length === 0 && !bothEmpty;

  return (
    <div className="literary-page page-section max-w-2xl mx-auto">
      <PageHeader
        icon="🪶"
        title={isOrg ? "Кабинет организации" : "Личный кабинет"}
        subtitle={`Добро пожаловать, ${user.full_name || user.username}`}
      >
        <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={logout}>Выйти</button>
      </PageHeader>

      <p className="literary-lead text-center mb-6 -mt-2">{PAGE_SECTIONS.cabinet.lead}</p>

      <div className="literary-quick-actions mb-6">
        <Link to="/complaints?new=1" className="literary-btn literary-btn--primary text-sm no-underline">⚠️ Обращение</Link>
        <Link to="/classifieds?new=1" className="literary-btn literary-btn--ghost text-sm no-underline">📋 Объявление</Link>
        <Link to="/events" className="literary-btn literary-btn--ghost text-sm no-underline">📅 Афиша</Link>
      </div>
      <p className="text-center text-sm text-muted-foreground mt-[-0.75rem] mb-5">
        Быстрый совет: сохраняйте короткое описание проблемы и номер телефона — так службе проще помочь быстрее.
      </p>

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

      {bothEmpty && (
        <LiteraryEmptyState {...EMPTY_STATES.complaintsMine} className="mb-6">
          <div className="flex flex-wrap justify-center gap-2">
            <Link to="/complaints?new=1" className="literary-btn literary-btn--primary text-sm no-underline">
              Подать обращение
            </Link>
            <Link to="/classifieds?new=1" className="literary-btn literary-btn--ghost text-sm no-underline">
              Подать объявление
            </Link>
          </div>
        </LiteraryEmptyState>
      )}

      {!issuesLoaded && <CabinetSectionSkeleton title="Мои обращения" />}

      {showIssuesEmpty && (
        <LiteraryEmptyState {...EMPTY_STATES.complaintsMine} compact className="mb-6">
          <Link to="/complaints?new=1" className="literary-btn literary-btn--primary text-sm no-underline mt-2">
            Подать обращение
          </Link>
        </LiteraryEmptyState>
      )}

      {recentIssues.length > 0 && (
        <div className="literary-card literary-card--gold p-6 mb-6 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="literary-title text-lg m-0">Мои обращения</h2>
            <div className="flex items-center gap-2">
              {activeIssues > 0 && (
                <span className="text-sm font-medium px-2 py-1 rounded-full bg-amber-100 text-amber-800">
                  {activeIssues} в работе
                </span>
              )}
              <Link to="/complaints" className="literary-link text-sm">Все →</Link>
            </div>
          </div>
          {recentIssues.map((issue) => (
            <div key={issue.id} className="border-t border-border pt-3 first:border-0 first:pt-0">
              <LiteraryIssueCard
                issue={issue}
                variant="link"
                href={`/complaints?issue=${issue.id}`}
                showStatusHint
                showResolution
              />
            </div>
          ))}
        </div>
      )}

      {!adsLoaded && <CabinetSectionSkeleton title="Мои объявления" lines={2} />}

      {showAdsEmpty && (
        <LiteraryEmptyState {...EMPTY_STATES.classifiedsMine} compact className="mb-6">
          <Link to="/classifieds?new=1" className="literary-btn literary-btn--ghost text-sm no-underline mt-2">
            Подать объявление
          </Link>
        </LiteraryEmptyState>
      )}

      {adsLoaded && myAds.length > 0 && (
        <div className="literary-card literary-card--forest p-6 mb-6 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="literary-title text-lg m-0">Мои объявления</h2>
            <Link to="/classifieds?new=1" className="literary-link text-sm">+ Новое</Link>
          </div>
          {myAds.map((ad) => (
            <div key={ad.id} className="border-t border-border pt-3 first:border-0 first:pt-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-base">{ad.title}</span>
                <span className={`cabinet-ad-status cabinet-ad-status--${ad.payment_status}`}>
                  {classifiedStatusLabel(ad)}
                </span>
              </div>
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2 m-0">{ad.description}</p>
            </div>
          ))}
          <p className="text-sm text-muted-foreground m-0 pt-2 border-t border-border/60">
            Отклонённые объявления не публикуются — проверьте текст и подайте заново.
          </p>
        </div>
      )}

      <div className="literary-cabinet-nav literary-cabinet-nav--comfort">
        <Link to="/classifieds?new=1" className="literary-useful-card literary-useful-card--gold no-underline text-inherit">
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
            <p className="literary-useful-desc">Обращения и статус рассмотрения</p>
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

      <div className="mt-6">
        <p className="text-sm text-muted-foreground text-center mb-3">{PAGE_SECTIONS.cabinet.vkHint}</p>
        <VkBotBanner />
      </div>
    </div>
  );
}
