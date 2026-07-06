/**
 * @vitest-environment jsdom
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { Complaints } from "./Complaints";

const createIssue = vi.fn();
const getCategories = vi.fn().mockResolvedValue([]);

vi.mock("@/lib/userAuth", () => ({
  useUserAuth: () => ({ user: null }),
}));

vi.mock("@/lib/api/index", () => ({
  api: {
    createIssue: (...args: unknown[]) => createIssue(...args),
    getCategories: () => getCategories(),
    getMyIssues: vi.fn(),
  },
}));

vi.mock("@/hooks/useFormDraft", () => {
  const React = require("react");
  return {
    useFormDraft: (_key: string, initial: object) => {
      const [value, setValue] = React.useState(initial);
      return { value, setValue, clearDraft: vi.fn() };
    },
  };
});

function renderComplaints() {
  return render(
    <MemoryRouter initialEntries={["/complaints?new=1"]}>
      <Complaints />
    </MemoryRouter>,
  );
}

describe("Complaints public form", () => {
  beforeEach(() => {
    createIssue.mockReset();
    createIssue.mockResolvedValue({ id: 42, status: "NEW" });
  });

  afterEach(() => {
    cleanup();
  });

  it("renders required guest fields and submit button", () => {
    renderComplaints();
    expect(screen.getByText("Подать обращение")).toBeTruthy();
    expect(screen.getByPlaceholderText("+7...")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Отправить обращение" })).toBeTruthy();
  });

  it("shows success only after API returns issue id", async () => {
    renderComplaints();
    fireEvent.change(screen.getByPlaceholderText("+7..."), {
      target: { value: "+79001300018" },
    });
    const nameInput = document.querySelector('input:not([placeholder="+7..."])') as HTMLInputElement;
    fireEvent.change(nameInput, { target: { value: "Module18 Test" } });
    fireEvent.change(
      screen.getByPlaceholderText("Например: не работает уличное освещение на перекрёстке..."),
      {
        target: { value: "MODULE 18 TEST — просьба не обрабатывать, проверка формы обращения." },
      },
    );
    fireEvent.click(screen.getByRole("button", { name: "Отправить обращение" }));

    await waitFor(() => {
      expect(createIssue).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(screen.getByText(/Обращение #\s*42/)).toBeTruthy();
    });
    expect(screen.getByText(/на рассмотрении/i)).toBeTruthy();
  });

  it("disables submit while request is pending", async () => {
    let resolveCreate: (v: { id: number; status: string }) => void = () => {};
    createIssue.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveCreate = resolve;
        }),
    );
    renderComplaints();
    fireEvent.change(screen.getByPlaceholderText("+7..."), {
      target: { value: "+79001300018" },
    });
    const nameInput = document.querySelector('input:not([placeholder="+7..."])') as HTMLInputElement;
    fireEvent.change(nameInput, { target: { value: "Test User" } });
    fireEvent.change(
      screen.getByPlaceholderText("Например: не работает уличное освещение на перекрёстке..."),
      { target: { value: "Достаточно длинный текст для проверки формы." } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Отправить обращение" }));

    await waitFor(() => {
      const pending = screen.getByRole("button", { name: "Отправляем…" }) as HTMLButtonElement;
      expect(pending.disabled).toBe(true);
    });
    resolveCreate({ id: 7, status: "NEW" });
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Отправить обращение" })).toBeTruthy();
    });
  });

  it("shows API error message on failure", async () => {
    createIssue.mockRejectedValue(new Error("Укажите имя и телефон"));
    renderComplaints();
    fireEvent.change(screen.getByPlaceholderText("+7..."), {
      target: { value: "+79001300018" },
    });
    const nameInput = document.querySelector('input:not([placeholder="+7..."])') as HTMLInputElement;
    fireEvent.change(nameInput, { target: { value: "Test User" } });
    fireEvent.change(
      screen.getByPlaceholderText("Например: не работает уличное освещение на перекрёстке..."),
      { target: { value: "Достаточно длинный текст для проверки формы." } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Отправить обращение" }));

    await waitFor(() => {
      expect(screen.getByText("Укажите имя и телефон")).toBeTruthy();
    });
  });
});
