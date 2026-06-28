import type { FormEvent, Ref } from "react";
import { LiterarySectionHead } from "./LiterarySectionHead";
import { Input } from "@/components/ui/input";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import type { ClassifiedAdFormState } from "@/lib/classifiedForm";
import { CLASSIFIED_FORM_TEMPLATES } from "@/lib/classifiedForm";

export type ClassifiedAdFormMode = "classifieds" | "jobs";

interface ClassifiedAdFormProps {
  mode: ClassifiedAdFormMode;
  categories: { value: string; label: string }[];
  form: ClassifiedAdFormState;
  setForm: (updater: ClassifiedAdFormState | ((prev: ClassifiedAdFormState) => ClassifiedAdFormState)) => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  formRef?: Ref<HTMLFormElement>;
  submitting?: boolean;
  showExtras: boolean;
  onToggleExtras: () => void;
  hints?: string[];
  kicker: string;
  title: string;
  lead?: string;
  freeTitle: string;
  freeLead: string;
  agreeLabel: string;
  submitLabel: string;
  showDraftNote?: boolean;
}

export function ClassifiedAdForm({
  mode,
  categories,
  form,
  setForm,
  onSubmit,
  formRef,
  submitting = false,
  showExtras,
  onToggleExtras,
  hints,
  kicker,
  title,
  lead,
  freeTitle,
  freeLead,
  agreeLabel,
  submitLabel,
  showDraftNote = false,
}: ClassifiedAdFormProps) {
  const isJobs = mode === "jobs";
  const idPrefix = isJobs ? "job" : "classified";

  return (
    <form
      ref={formRef}
      onSubmit={onSubmit}
      className={`page-panel page-panel--forest mb-8 space-y-4 form-glow${!isJobs ? " literary-form-comfort" : ""}`}
    >
      <LiterarySectionHead kicker={kicker} title={title} lead={lead} compact={!isJobs} />

      <div className="free-banner">
        <span className="text-lg">🆓</span>
        <div>
          <p className="font-bold m-0">{freeTitle}</p>
          <p className="text-sm text-muted-foreground m-0 mt-1">{freeLead}</p>
        </div>
      </div>

      {hints && hints.length > 0 && (
        <ul className="literary-form-hints">
          {hints.map((h) => (
            <li key={h}>{h}</li>
          ))}
        </ul>
      )}

      <label htmlFor={`${idPrefix}-category`} className={isJobs ? "sr-only" : "event-detail-label"}>
        Категория
      </label>
      <select
        id={`${idPrefix}-category`}
        className="pushkin-select w-full"
        value={form.category}
        onChange={(e) => setForm({ ...form, category: e.target.value })}
      >
        {categories.map((c) => (
          <option key={c.value} value={c.value}>
            {getCategoryVisual(c.value).icon} {c.label}
          </option>
        ))}
      </select>

      {!isJobs && (
        <label htmlFor={`${idPrefix}-title`} className="event-detail-label">Заголовок объявления</label>
      )}
      <Input
        id={`${idPrefix}-title`}
        placeholder={isJobs ? "Должность, напр. Продавец-кассир" : "Например: Продам сухие дрова"}
        value={form.title}
        onChange={(e) => setForm({ ...form, title: e.target.value })}
        required
      />

      {!isJobs && (
        <label htmlFor={`${idPrefix}-description`} className="event-detail-label">Описание</label>
      )}
      <textarea
        id={`${idPrefix}-description`}
        className="literary-textarea w-full min-h-[100px]"
        placeholder={
          isJobs
            ? "Обязанности, график, требования, как связаться…"
            : "Что предлагаете, в каком состоянии, как связаться"
        }
        value={form.description}
        onChange={(e) => setForm({ ...form, description: e.target.value })}
        required
      />

      {!isJobs && (
        <>
          <div className="suggest-chips">
            {CLASSIFIED_FORM_TEMPLATES.map((template) => (
              <button
                key={template}
                type="button"
                className="suggest-chip"
                onClick={() => setForm((f) => ({ ...f, description: template }))}
              >
                {template}
              </button>
            ))}
          </div>
          <p className="text-sm text-muted-foreground m-0 -mt-2">
            Чем проще и короче текст, тем быстрее отклик.
            <span className={`form-char-count${form.description.trim().length < 15 ? " form-char-count--warn" : ""}`}>
              {" "}
              {form.description.trim().length} симв. (минимум 15)
            </span>
          </p>
        </>
      )}

      {isJobs ? (
        <div className="grid grid-cols-2 gap-2">
          <Input
            type="number"
            placeholder="Зарплата / ставка"
            value={form.price}
            onChange={(e) => setForm({ ...form, price: e.target.value })}
          />
          <Input
            placeholder="за смену, месяц, сезон…"
            value={form.price_unit}
            onChange={(e) => setForm({ ...form, price_unit: e.target.value })}
          />
        </div>
      ) : (
        <>
          <label htmlFor={`${idPrefix}-phone`} className="event-detail-label">Телефон для связи</label>
          <Input
            id={`${idPrefix}-phone`}
            placeholder="+7 9XX XXX-XX-XX"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            required
          />
          <label htmlFor={`${idPrefix}-author`} className="event-detail-label">Ваше имя</label>
          <Input
            id={`${idPrefix}-author`}
            placeholder="Как к вам обращаться"
            value={form.author_name}
            onChange={(e) => setForm({ ...form, author_name: e.target.value })}
            required
          />
          <button
            type="button"
            className="literary-btn literary-btn--ghost text-sm w-full"
            onClick={onToggleExtras}
          >
            {showExtras ? "Скрыть дополнительно" : "Цена, адрес и ВК (необязательно)"}
          </button>
        </>
      )}

      {(isJobs || showExtras) && (
        <>
          {!isJobs && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div>
                <label htmlFor={`${idPrefix}-price`} className="event-detail-label">Цена</label>
                <Input
                  id={`${idPrefix}-price`}
                  type="number"
                  placeholder="Ваша цена"
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                />
              </div>
              <div>
                <label htmlFor={`${idPrefix}-price-unit`} className="event-detail-label">За что цена</label>
                <Input
                  id={`${idPrefix}-price-unit`}
                  placeholder="за смену, месяц, штуку"
                  value={form.price_unit}
                  onChange={(e) => setForm({ ...form, price_unit: e.target.value })}
                />
              </div>
            </div>
          )}
          {!isJobs && (
            <label htmlFor={`${idPrefix}-address`} className="event-detail-label">Адрес или район</label>
          )}
          <Input
            id={`${idPrefix}-address`}
            placeholder={isJobs ? "Адрес / посёлок" : "Где забрать или где оказать услугу"}
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
          />
          {!isJobs && (
            <label htmlFor={`${idPrefix}-vk`} className="event-detail-label">Контакт VK (необязательно)</label>
          )}
          <Input
            id={`${idPrefix}-vk`}
            placeholder={
              isJobs
                ? "VK — уведомим о публикации"
                : "ВКонтакте (id или ссылка) — уведомим о публикации в VK"
            }
            value={form.contact_vk}
            onChange={(e) => setForm({ ...form, contact_vk: e.target.value })}
          />
        </>
      )}

      {isJobs && (
        <>
          <Input
            placeholder="Телефон работодателя +7…"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            required
          />
          <Input
            placeholder="Название организации или ФИО"
            value={form.author_name}
            onChange={(e) => setForm({ ...form, author_name: e.target.value })}
            required
          />
        </>
      )}

      <input
        type="text"
        name="website_url"
        value={form.website_url}
        onChange={(e) => setForm({ ...form, website_url: e.target.value })}
        className="honeypot-field"
        tabIndex={-1}
        autoComplete="off"
        aria-hidden
      />
      <label className="flex items-start gap-2 text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={form.agree_rules}
          onChange={(e) => setForm({ ...form, agree_rules: e.target.checked })}
          className="mt-1"
          required
        />
        <span>{agreeLabel}</span>
      </label>
      <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={submitting}>
        {submitting ? "Отправляем…" : submitLabel}
      </button>
      {showDraftNote && (
        <p className="text-sm text-muted-foreground text-center m-0">Черновик сохраняется автоматически.</p>
      )}
    </form>
  );
}
