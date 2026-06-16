/** Shared classified / jobs ad form state. */

export interface ClassifiedAdFormState extends Record<string, unknown> {
  category: string;
  title: string;
  description: string;
  price: string;
  price_unit: string;
  phone: string;
  author_name: string;
  address: string;
  contact_vk: string;
  website_url: string;
  agree_rules: boolean;
}

export const CLASSIFIED_FORM_INITIAL: ClassifiedAdFormState = {
  category: "firewood",
  title: "",
  description: "",
  price: "",
  price_unit: "₽",
  phone: "",
  author_name: "",
  address: "",
  contact_vk: "",
  website_url: "",
  agree_rules: false,
};

export const JOBS_FORM_INITIAL: ClassifiedAdFormState = {
  category: "job_tourism",
  title: "",
  description: "",
  price: "",
  price_unit: "₽/мес",
  phone: "",
  author_name: "",
  address: "",
  contact_vk: "",
  website_url: "",
  agree_rules: false,
};

export const CLASSIFIEDS_DRAFT_KEY = "classifieds_form_draft_v1";
export const JOBS_DRAFT_KEY = "jobs_form_draft_v1";

export const CLASSIFIED_FORM_TEMPLATES = [
  "Продам: в хорошем состоянии, самовывоз.",
  "Услуга: аккуратно и в срок, без предоплаты.",
  "Соседская помощь: могу помочь в выходные.",
];
