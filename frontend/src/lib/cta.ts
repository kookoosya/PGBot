/** Единые подписи кнопок и ссылок по порталу */
export const CTA = {
  open: "Открыть",
  details: "Подробнее",
  allEvents: "Вся афиша",
  allJobs: "Все вакансии",
  allClassifieds: "Все объявления",
  backHome: "На главную",
  backEvents: "К афише",
  submitComplaint: "Подать обращение",
  submitClassified: "Подать объявление",
  postJob: "Разместить вакансию",
} as const;

export function ctaArrow(label: string): string {
  return `${label} →`;
}
