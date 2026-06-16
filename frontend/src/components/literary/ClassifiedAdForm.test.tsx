/**
 * @vitest-environment jsdom
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { CLASSIFIED_FORM_INITIAL } from "@/lib/classifiedForm";
import { ClassifiedAdForm } from "./ClassifiedAdForm";

const categories = [
  { value: "firewood", label: "Дрова" },
  { value: "services", label: "Услуги" },
];

function renderClassified(overrides: Record<string, unknown> = {}) {
  const form = { ...CLASSIFIED_FORM_INITIAL, agree_rules: true };
  const setForm = vi.fn();
  const onToggleExtras = vi.fn();
  const view = render(
    <ClassifiedAdForm
      mode="classifieds"
      categories={categories}
      form={form}
      setForm={setForm}
      onSubmit={(e) => e.preventDefault()}
      showExtras={false}
      onToggleExtras={onToggleExtras}
      kicker="✍️ Публикация"
      title="Разместить объявление"
      lead="Бесплатно после модерации"
      freeTitle="Бесплатно"
      freeLead="Без комиссии"
      agreeLabel="Согласен с правилами"
      submitLabel="Отправить"
      {...overrides}
    />,
  );
  return { ...view, form, setForm, onToggleExtras };
}

afterEach(() => {
  cleanup();
});

describe("ClassifiedAdForm", () => {
  it("renders classifieds fields and section head", () => {
    renderClassified();
    expect(screen.getByText("Разместить объявление")).toBeTruthy();
    expect(screen.getByLabelText("Телефон для связи")).toBeTruthy();
    expect(screen.getByLabelText("Ваше имя")).toBeTruthy();
  });

  it("uses job field ids in jobs mode", () => {
    const { container } = renderClassified({ mode: "jobs" });
    expect(container.querySelector("#job-title")).toBeTruthy();
    expect(container.querySelector("#classified-title")).toBeNull();
    expect(screen.getByPlaceholderText(/Телефон работодателя/)).toBeTruthy();
  });

  it("applies suggest template to description", () => {
    const { setForm, container } = renderClassified();
    const chip = within(container).getByRole("button", {
      name: "Продам: в хорошем состоянии, самовывоз.",
    });
    fireEvent.click(chip);
    expect(setForm).toHaveBeenCalled();
  });

  it("toggles extras section", () => {
    const { onToggleExtras, container } = renderClassified();
    const toggle = within(container).getByRole("button", {
      name: "Цена, адрес и ВК (необязательно)",
    });
    fireEvent.click(toggle);
    expect(onToggleExtras).toHaveBeenCalledOnce();
  });

  it("shows extra price fields when showExtras is true", () => {
    renderClassified({ showExtras: true });
    expect(screen.getByLabelText("Цена")).toBeTruthy();
    expect(screen.getByLabelText("Адрес или район")).toBeTruthy();
  });

  it("disables submit while submitting", () => {
    renderClassified({ submitting: true });
    const submit = screen.getByRole("button", { name: "Отправляем…" });
    expect((submit as HTMLButtonElement).disabled).toBe(true);
  });

  it("updates form via setForm on title change", () => {
    const { setForm, container } = renderClassified();
    const titleInput = container.querySelector("#classified-title") as HTMLInputElement;
    fireEvent.change(titleInput, { target: { value: "Дрова" } });
    expect(setForm).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Дрова" }),
    );
  });
});
