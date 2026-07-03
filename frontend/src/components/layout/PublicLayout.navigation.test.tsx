/**
 * @vitest-environment jsdom
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { PublicLayout } from "./PublicLayout";

vi.mock("@/lib/userAuth", () => ({
  useUserAuth: () => ({ user: null }),
}));

const trackVisit = vi.fn().mockResolvedValue(undefined);

vi.mock("@/lib/api/index", () => ({
  api: {
    trackVisit: (...args: unknown[]) => trackVisit(...args),
  },
}));

vi.mock("@/components/PageBackdrop", () => ({
  PageBackdrop: () => null,
}));

vi.mock("@/components/FooterNav", () => ({
  FooterNav: () => <nav aria-label="footer" />,
}));

vi.mock("@/components/VkBotLink", () => ({
  VkBotLink: () => null,
}));

vi.mock("@/components/weather/WeatherWidgetCompact", () => ({
  WeatherWidgetCompact: () => null,
}));

function HomeProbe() {
  return <h1>Главная probe</h1>;
}

function MapProbe() {
  return <h1>Карта probe</h1>;
}

function EventsProbe() {
  return <h1>Афиша probe</h1>;
}

function ServicesProbe() {
  return <h1>Услуги probe</h1>;
}

function renderPortal(initial = "/") {
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <PublicLayout />,
        children: [
          { index: true, element: <HomeProbe /> },
          { path: "map", element: <MapProbe /> },
          { path: "events", element: <EventsProbe /> },
          { path: "services", element: <ServicesProbe /> },
        ],
      },
    ],
    { initialEntries: [initial] },
  );
  render(<RouterProvider router={router} />);
  return router;
}

function topTab(href: string) {
  return document.querySelector(`nav.pushkin-tab-bar-top a[href="${href}"]`) as HTMLAnchorElement;
}

function bottomTab(href: string) {
  return document.querySelector(`nav.pushkin-tab-bar-bottom a[href="${href}"]`) as HTMLAnchorElement;
}

describe("PublicLayout navigation performance", () => {
  beforeEach(() => {
    trackVisit.mockClear();
    document.body.innerHTML = "";
  });

  it("keeps the same main element across route changes (no pathname key remount)", async () => {
    const router = renderPortal("/");
    const mainBefore = document.querySelector("main.pushkin-main");
    expect(mainBefore).toBeTruthy();

    await router.navigate("/map");
    await waitFor(() => expect(screen.getByRole("heading", { name: /Карта probe/i })).toBeTruthy());

    const mainAfter = document.querySelector("main.pushkin-main");
    expect(mainAfter).toBe(mainBefore);
  });

  it("clicking a tab changes route", async () => {
    const router = renderPortal("/");
    topTab("/events").click();
    await waitFor(() => expect(router.state.location.pathname).toBe("/events"));
    expect(screen.getByRole("heading", { name: /Афиша probe/i })).toBeTruthy();
  });

  it("shows section content without blank main on navigation", async () => {
    const router = renderPortal("/");
    await router.navigate("/services");
    await waitFor(() => expect(screen.getByRole("heading", { name: /Услуги probe/i })).toBeTruthy());
    const main = document.querySelector("main.pushkin-main");
    expect(main?.textContent?.length ?? 0).toBeGreaterThan(0);
  });

  it("supports back navigation", async () => {
    const router = renderPortal("/");
    await router.navigate("/map");
    await waitFor(() => expect(screen.getByRole("heading", { name: /Карта probe/i })).toBeTruthy());
    await router.navigate(-1);
    await waitFor(() => expect(screen.getByRole("heading", { name: /Главная probe/i })).toBeTruthy());
  });

  it("supports forward navigation", async () => {
    const router = renderPortal("/");
    await router.navigate("/map");
    await router.navigate(-1);
    await router.navigate(1);
    await waitFor(() => expect(screen.getByRole("heading", { name: /Карта probe/i })).toBeTruthy());
  });

  it("loads direct routes", async () => {
    renderPortal("/events");
    expect(screen.getByRole("heading", { name: /Афиша probe/i })).toBeTruthy();
  });

  it("mobile bottom navigation works", async () => {
    const router = renderPortal("/");
    bottomTab("/map").click();
    await waitFor(() => expect(router.state.location.pathname).toBe("/map"));
  });

  it("desktop top navigation works", async () => {
    const router = renderPortal("/");
    topTab("/map").click();
    await waitFor(() => expect(router.state.location.pathname).toBe("/map"));
  });

  it("fires one trackVisit per navigation, not duplicate on same path", async () => {
    const router = renderPortal("/");
    await router.navigate("/map");
    await router.navigate("/events");
    const paths = trackVisit.mock.calls.map((c) => c[0]);
    expect(paths.filter((p) => p === "/map").length).toBeLessThanOrEqual(1);
    expect(paths.filter((p) => p === "/events").length).toBeLessThanOrEqual(1);
  });

  it("ten transitions complete without throwing", async () => {
    const router = renderPortal("/");
    const cycle = ["/map", "/events", "/services", "/"];
    for (let i = 0; i < 10; i++) {
      await router.navigate(cycle[i % cycle.length]);
    }
    expect(["/", "/map", "/events", "/services"]).toContain(router.state.location.pathname);
  });
});
