import { geoNavigateUrl, yandexMapsPointUrl, yandexRouteUrl } from "@/lib/mapLinks";
import { Button } from "@/components/ui/button";
import type { ComplaintType } from "@/lib/api/types/issues";
import type { PlaceDetail } from "@/lib/api/types/places";
import { CATEGORY_ICONS } from "./constants";
import { RatingBadge } from "./RatingBadge";
import { formatPlaceNote } from "./utils";
import type { MapPageState } from "./useMapPage";

type PlaceDetailPanelProps = Pick<
  MapPageState,
  | "selected"
  | "tab"
  | "setTab"
  | "msg"
  | "msgType"
  | "reviewForm"
  | "setReviewForm"
  | "complaintForm"
  | "setComplaintForm"
  | "reportForm"
  | "setReportForm"
  | "complaintTypes"
  | "mapReportTypes"
  | "submitReview"
  | "submitComplaint"
  | "submitReport"
  | "clearSelection"
> & {
  selected: PlaceDetail;
};

export function PlaceDetailPanel({
  selected,
  tab,
  setTab,
  msg,
  msgType,
  reviewForm,
  setReviewForm,
  complaintForm,
  setComplaintForm,
  reportForm,
  setReportForm,
  complaintTypes,
  mapReportTypes,
  submitReview,
  submitComplaint,
  submitReport,
  clearSelection,
}: PlaceDetailPanelProps) {
  return (
    <div className="p-4 org-detail-card page-panel page-panel--gold literary-map-detail">
      <button type="button" className="literary-btn literary-btn--ghost text-sm mb-3" onClick={clearSelection}>
        ← К списку
      </button>

      <div className="org-detail-header">
        <span className="org-detail-icon">{CATEGORY_ICONS[selected.category] || "📍"}</span>
        <div>
          <h3 className="text-xl font-bold leading-tight">{selected.name}</h3>
          <p className="text-sm text-muted-foreground">{selected.category_label}</p>
        </div>
      </div>

      <RatingBadge place={selected} />

      {selected.rating_source === "reference" && (
        <p className="map-ref-badge m-0 mt-2">
          ✓ Координаты и адрес проверены справочником посёлка
        </p>
      )}

      {selected.address && <p className="org-detail-row">📍 {selected.address}</p>}
      {selected.opening_hours && (
        <div className="org-hours-box">
          <p className="font-medium">🕐 {selected.opening_hours}</p>
        </div>
      )}
      {selected.phone && (
        <p className="org-detail-row">
          📞 <a href={`tel:${selected.phone.replace(/\s/g, "")}`} className="clickable-phone">{selected.phone}</a>
        </p>
      )}
      {selected.website && (
        <p className="org-detail-row">
          🔗{" "}
          <a href={selected.website} target="_blank" rel="noopener noreferrer">
            Сайт
          </a>
        </p>
      )}
      {formatPlaceNote(selected.description) && (
        <p className="text-sm text-muted-foreground mt-2">{formatPlaceNote(selected.description)}</p>
      )}
      <p className="text-xs text-muted-foreground mt-2 m-0">
        Данные из открытых источников — уточняйте часы и телефон перед визитом.
      </p>

      <div className="org-action-grid mt-4">
        {selected.phone && (
          <a href={`tel:${selected.phone.replace(/\s/g, "")}`} className="org-action-btn org-action-call no-underline">
            📞 Позвонить
          </a>
        )}
        <a
          href={yandexRouteUrl(selected.latitude, selected.longitude)}
          target="_blank"
          rel="noopener noreferrer"
          className="org-action-btn org-action-route no-underline"
        >
          🧭 Маршрут
        </a>
        <a
          href={selected.yandex_url || yandexMapsPointUrl(selected.latitude, selected.longitude, selected.name)}
          target="_blank"
          rel="noopener noreferrer"
          className="org-action-btn org-action-maps no-underline"
        >
          🗺 На карте
        </a>
        <a href={geoNavigateUrl(selected.latitude, selected.longitude)} className="org-action-btn org-action-offline no-underline">
          📍 GPS
        </a>
      </div>

      <div className="org-tabs mt-4">
        {(["info", "review", "report", "complaint"] as const).map((t) => (
          <button
            key={t}
            type="button"
            className={`org-tab${tab === t ? " org-tab-active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t === "info" ? "Отзывы" : t === "review" ? "Оценить" : t === "report" ? "Ошибка" : "Претензия"}
          </button>
        ))}
      </div>

      {msg && (
        <p className={`text-sm mt-2 ${msgType === "ok" ? "text-green-700" : "text-destructive"}`}>
          {msg}
        </p>
      )}

      {tab === "info" && (
        <div className="mt-3 space-y-2">
          {selected.reviews.length === 0 && <p className="text-sm text-muted-foreground">Отзывов жителей пока нет — оцените первым!</p>}
          {selected.reviews.map((r) => (
            <div key={r.id} className="org-review-card">
              <span>{"★".repeat(r.rating)}</span> <strong>{r.author_name}</strong>
              <p>{r.text}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "review" && (
        <div className="mt-3 space-y-3">
          <select className="w-full border rounded px-2 py-1" value={reviewForm.rating} onChange={(e) => setReviewForm({ ...reviewForm, rating: +e.target.value })}>
            {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{"★".repeat(n)}</option>)}
          </select>
          <textarea className="w-full border rounded p-2 text-sm min-h-[80px]" placeholder="Ваш отзыв..." value={reviewForm.text} onChange={(e) => setReviewForm({ ...reviewForm, text: e.target.value })} />
          <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Ваше имя" value={reviewForm.author_name} onChange={(e) => setReviewForm({ ...reviewForm, author_name: e.target.value })} />
          <Button className="w-full" onClick={submitReview}>Отправить отзыв</Button>
        </div>
      )}

      {tab === "report" && (
        <div className="mt-3 space-y-3">
          <p className="text-xs text-muted-foreground m-0">Заведение закрылось? Неверный телефон? Напишите — обновим карту.</p>
          <select className="w-full border rounded px-2 py-1 text-sm" value={reportForm.complaint_type} onChange={(e) => setReportForm({ ...reportForm, complaint_type: e.target.value })}>
            {mapReportTypes.map((t: ComplaintType) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <textarea className="w-full border rounded p-2 text-sm min-h-[80px]" placeholder="Что не так? Например: закрыто, другой телефон..." value={reportForm.description} onChange={(e) => setReportForm({ ...reportForm, description: e.target.value })} />
          <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Ваше имя (необязательно)" value={reportForm.author_name} onChange={(e) => setReportForm({ ...reportForm, author_name: e.target.value })} />
          <Button className="w-full" disabled={reportForm.description.length < 10} onClick={submitReport}>
            Отправить
          </Button>
        </div>
      )}

      {tab === "complaint" && (
        <div className="mt-3 space-y-3">
          <p className="text-xs text-muted-foreground m-0">Претензия к заведению: цена, чек, товар.</p>
          <select className="w-full border rounded px-2 py-1 text-sm" value={complaintForm.complaint_type} onChange={(e) => setComplaintForm({ ...complaintForm, complaint_type: e.target.value })}>
            {complaintTypes.map((t: ComplaintType) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <div className="grid grid-cols-2 gap-2">
            <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Цена на ценнике" value={complaintForm.price_tagged} onChange={(e) => setComplaintForm({ ...complaintForm, price_tagged: e.target.value })} />
            <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Взяли с вас" value={complaintForm.price_charged} onChange={(e) => setComplaintForm({ ...complaintForm, price_charged: e.target.value })} />
          </div>
          <textarea className="w-full border rounded p-2 text-sm min-h-[100px]" placeholder="Опишите ситуацию (мин. 10 символов)..." value={complaintForm.description} onChange={(e) => setComplaintForm({ ...complaintForm, description: e.target.value })} />
          <Button className="w-full" variant="destructive" disabled={complaintForm.description.length < 10} onClick={submitComplaint}>
            Отправить претензию
          </Button>
        </div>
      )}
    </div>
  );
}
