/** @vitest-environment jsdom */
import { describe, expect, it } from "vitest";
import { renderHook } from "@testing-library/react";
import { useDocumentTitle } from "./useDocumentTitle";

describe("useDocumentTitle", () => {
  it("sets and restores document title", () => {
    const original = document.title;
    const { unmount } = renderHook(({ title }) => useDocumentTitle(title), {
      initialProps: { title: "Афиша" },
    });
    expect(document.title).toBe("Афиша — Пушкинские Горы");
    unmount();
    expect(document.title).toBe(original);
  });
});
