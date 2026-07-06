/**
 * @vitest-environment jsdom
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useIssuesWorkbench } from "./useIssuesWorkbench";

const getIssues = vi.fn();
const getIssue = vi.fn();
const updateIssueStatus = vi.fn();

vi.mock("@/lib/api/index", () => ({
  api: {
    getIssues: (...args: unknown[]) => getIssues(...args),
    getIssue: (...args: unknown[]) => getIssue(...args),
    updateIssueStatus: (...args: unknown[]) => updateIssueStatus(...args),
  },
}));

describe("useIssuesWorkbench", () => {
  beforeEach(() => {
    getIssues.mockReset();
    getIssue.mockReset();
    updateIssueStatus.mockReset();
    getIssues.mockResolvedValue({ items: [], total: 0 });
  });

  it("loads issues on mount", async () => {
    const { result } = renderHook(() => useIssuesWorkbench());
    await waitFor(() => expect(getIssues).toHaveBeenCalled());
    expect(getIssues.mock.calls[0][0]).toEqual({ page: "1", page_size: "20" });
    expect(result.current.issues).toEqual([]);
    expect(result.current.totalPages).toBe(1);
  });

  it("applies status change and reloads", async () => {
    getIssues.mockResolvedValue({
      items: [{ id: 5, resolution_text: null, status: "NEW" }],
      total: 1,
    });
    getIssue.mockResolvedValue({ id: 5, status: "RESOLVED", resolution_text: "Готово" });
    updateIssueStatus.mockResolvedValue({});

    const { result } = renderHook(() => useIssuesWorkbench());
    await waitFor(() => expect(result.current.issues).toHaveLength(1));

    await act(async () => {
      await result.current.handleStatusChange(result.current.issues[0] as never, "RESOLVED");
    });

    expect(updateIssueStatus).toHaveBeenCalledWith(5, "RESOLVED", undefined);
    expect(getIssues).toHaveBeenCalledTimes(2);
  });

  it("stores status update error message", async () => {
    getIssues.mockResolvedValue({
      items: [{ id: 5, resolution_text: null, status: "NEW" }],
      total: 1,
    });
    updateIssueStatus.mockRejectedValue(new Error("Недостаточно прав"));

    const { result } = renderHook(() => useIssuesWorkbench());
    await waitFor(() => expect(result.current.issues).toHaveLength(1));

    await act(async () => {
      await result.current.handleStatusChange(result.current.issues[0] as never, "RESOLVED");
    });

    expect(result.current.statusError).toBe("Недостаточно прав");
  });
});
