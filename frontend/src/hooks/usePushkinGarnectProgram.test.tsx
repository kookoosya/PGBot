/** @vitest-environment jsdom */
import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { usePushkinGarnectProgram } from "./usePushkinGarnectProgram";

const getPublicEvents = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api/index", () => ({ api: { getPublicEvents } }));

describe("local event preview outage and recovery", () => {
  it("distinguishes an unavailable API from a verified empty response", async () => {
    getPublicEvents.mockRejectedValueOnce(new Error("offline"));
    const { result } = renderHook(() => usePushkinGarnectProgram());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe("Афиша недоступна");

    getPublicEvents.mockResolvedValueOnce({ items: [] });
    await act(async () => { await result.current.refresh(); });
    expect(result.current.error).toBeNull();
    expect(result.current.program).toEqual([]);
    expect(getPublicEvents).toHaveBeenCalledTimes(2);
  });
});
