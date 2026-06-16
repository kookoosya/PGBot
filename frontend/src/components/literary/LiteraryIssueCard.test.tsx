/**
 * @vitest-environment jsdom
 */
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { Issue } from "@/lib/api";
import { LiteraryIssueCard } from "./LiteraryIssueCard";

const baseIssue: Issue = {
  id: 42,
  title: null,
  description: "Сломан фонарь на улице",
  status: "NEW",
  category: "roads",
  priority: "medium",
  address: "ул. Ленина, 5",
  resident_id: 1,
  department_id: null,
  assignee_id: null,
  confirmation_count: 0,
  is_spam: false,
  resolution_text: null,
  resolved_at: null,
  created_at: "2026-06-01T10:00:00Z",
  updated_at: "2026-06-01T10:00:00Z",
  photos: [],
  ai_analysis: {
    is_valid: true,
    category: "roads",
    priority: "medium",
    summary: "Фонарь не горит у школы",
    duplicate_probability: null,
    suggested_department: null,
  },
};

function renderCard(ui: ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("LiteraryIssueCard", () => {
  it("renders AI summary and address", () => {
    renderCard(<LiteraryIssueCard issue={baseIssue} />);
    expect(screen.getByText("#42")).toBeTruthy();
    expect(screen.getByText("Фонарь не горит у школы")).toBeTruthy();
    expect(screen.getByText(/ул\. Ленина/)).toBeTruthy();
  });

  it("falls back to description when AI summary missing", () => {
    const issue = { ...baseIssue, ai_analysis: null };
    renderCard(<LiteraryIssueCard issue={issue} />);
    expect(screen.getByText("Сломан фонарь на улице")).toBeTruthy();
  });

  it("shows status hint when enabled", () => {
    renderCard(<LiteraryIssueCard issue={baseIssue} showStatusHint />);
    expect(screen.getByText(/ожидает рассмотрения/i)).toBeTruthy();
  });

  it("calls onClick for selectable variant", () => {
    const onClick = vi.fn();
    renderCard(
      <LiteraryIssueCard issue={baseIssue} variant="selectable" onClick={onClick} />,
    );
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("renders timeline and resolution blocks", () => {
    const issue: Issue = {
      ...baseIssue,
      status: "RESOLVED",
      resolution_text: "Фонарь заменён",
      status_timeline: [
        {
          status: "NEW",
          label: "Принято",
          at: "2026-06-01T10:00:00Z",
          previous_status: null,
        },
        {
          status: "RESOLVED",
          label: "Решено",
          at: "2026-06-02T12:00:00Z",
          previous_status: "NEW",
          resolution: "Фонарь заменён",
        },
      ],
    };
    renderCard(
      <LiteraryIssueCard issue={issue} showTimeline showResolution />,
    );
    expect(screen.getByText("История статусов")).toBeTruthy();
    expect(screen.getByText("Ответ службы:")).toBeTruthy();
    expect(screen.getAllByText("Фонарь заменён").length).toBeGreaterThanOrEqual(1);
  });

  it("renders link variant with href", () => {
    renderCard(
      <LiteraryIssueCard issue={baseIssue} variant="link" href="/complaints/42" />,
    );
    const link = screen.getByRole("link");
    expect(link.getAttribute("href")).toBe("/complaints/42");
  });
});
