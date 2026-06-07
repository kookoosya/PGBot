import { Link, Navigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useUserAuth } from "@/lib/userAuth";

const STATUS_LABELS: Record<string, { text: string; tone: string }> = {
  pending: { text: "На проверке — мы свяжемся с вами", tone: "text-amber-700 bg-amber-50 border-amber-200" },
  approved: { text: "Подтверждено", tone: "text-green-700 bg-green-50 border-green-200" },
  rejected: { text: "Заявка отклонена — напишите нам", tone: "text-red-700 bg-red-50 border-red-200" },
};

export function UserCabinet() {
  const { user, loading, logout } = useUserAuth();

  if (loading) {
    return <div className="page-section text-center text-muted-foreground">Загрузка кабинета...</div>;
  }

  if (!user) return <Navigate to="/cabinet/login" replace />;

  const status = user.verification_status ? STATUS_LABELS[user.verification_status] : null;

  return (
    <div className="page-section max-w-2xl mx-auto">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold">Личный кабинет</h1>
          <p className="text-muted-foreground mt-1">
            Здравствуйте, {user.full_name || user.username}!
          </p>
        </div>
        <Button variant="outline" onClick={logout}>
          Выйти
        </Button>
      </div>

      <div className="pushkin-card p-6 space-y-4 mb-6">
        <h2 className="font-semibold text-lg">Ваш профиль</h2>
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

      <div className="human-note mb-6">
        <p className="m-0 text-sm">
          Это ваш уголок на портале посёлка: объявления, отзывы на карте, запись к мастерам.
          Данные на карте обновляются автоматически — магазины, аптеки и службы подтягиваются из справочников.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Link to="/classifieds" className="register-option-card no-underline text-inherit">
          <span className="text-3xl">📋</span>
          <div>
            <h3 className="font-bold m-0">Объявления</h3>
            <p className="text-sm text-muted-foreground mt-1 mb-0">Подать объявление жителям посёлка</p>
          </div>
        </Link>
        <Link to="/map" className="register-option-card no-underline text-inherit">
          <span className="text-3xl">🗺</span>
          <div>
            <h3 className="font-bold m-0">Карта</h3>
            <p className="text-sm text-muted-foreground mt-1 mb-0">Организации, отзывы, такси</p>
          </div>
        </Link>
        <Link to="/services" className="register-option-card no-underline text-inherit">
          <span className="text-3xl">💇</span>
          <div>
            <h3 className="font-bold m-0">Услуги</h3>
            <p className="text-sm text-muted-foreground mt-1 mb-0">Записаться к мастеру</p>
          </div>
        </Link>
        <Link to="/services/register" className="register-option-card no-underline text-inherit">
          <span className="text-3xl">📅</span>
          <div>
            <h3 className="font-bold m-0">Стать мастером</h3>
            <p className="text-sm text-muted-foreground mt-1 mb-0">Расписание и записи клиентов</p>
          </div>
        </Link>
      </div>
    </div>
  );
}
