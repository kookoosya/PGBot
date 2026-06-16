import bridge from "@vkontakte/vk-bridge";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { isVkEnvironment } from "@/lib/vkBridge";

export type VkTab = "events" | "classifieds" | "issues";

export type VkScreen =
  | { type: "tab" }
  | { type: "event"; id: number }
  | { type: "classified"; id: number }
  | { type: "issue"; id: number }
  | { type: "profile" }
  | { type: "help" };

interface VkNavigationContextValue {
  tab: VkTab;
  stack: VkScreen[];
  current: VkScreen;
  setTab: (tab: VkTab) => void;
  openEvent: (id: number) => void;
  openClassified: (id: number) => void;
  openIssue: (id: number) => void;
  openProfile: () => void;
  openHelp: () => void;
  goBack: () => void;
  canGoBack: boolean;
  isDetailView: boolean;
  isOverlayView: boolean;
}

const VkNavigationContext = createContext<VkNavigationContextValue | null>(null);

function screenKey(screen: VkScreen): string {
  if (screen.type === "tab") return "tab";
  if (screen.type === "profile") return "profile";
  if (screen.type === "help") return "help";
  return `${screen.type}:${screen.id}`;
}

export function VkNavigationProvider({ children }: { children: React.ReactNode }) {
  const [tab, setTabState] = useState<VkTab>("events");
  const [stack, setStack] = useState<VkScreen[]>([{ type: "tab" }]);

  const push = useCallback((screen: VkScreen) => {
    setStack((prev) => {
      const key = screenKey(screen);
      if (screenKey(prev[prev.length - 1]) === key) return prev;
      return [...prev, screen];
    });
  }, []);

  const setTab = useCallback((next: VkTab) => {
    setTabState(next);
    setStack([{ type: "tab" }]);
  }, []);

  const goBack = useCallback(() => {
    setStack((prev) => (prev.length > 1 ? prev.slice(0, -1) : prev));
  }, []);

  const openEvent = useCallback((id: number) => push({ type: "event", id }), [push]);
  const openClassified = useCallback((id: number) => push({ type: "classified", id }), [push]);
  const openIssue = useCallback((id: number) => push({ type: "issue", id }), [push]);
  const openProfile = useCallback(() => push({ type: "profile" }), [push]);
  const openHelp = useCallback(() => push({ type: "help" }), [push]);

  const current = stack[stack.length - 1] ?? { type: "tab" };
  const canGoBack = stack.length > 1;
  const isDetailView = current.type === "event" || current.type === "classified" || current.type === "issue";
  const isOverlayView = current.type === "profile" || current.type === "help";

  useEffect(() => {
    if (!isVkEnvironment() || !canGoBack) return;

    const onBridgeEvent = (event: { detail?: { type?: string } }) => {
      if (event.detail?.type === "VKWebAppBack") {
        goBack();
      }
    };

    bridge.subscribe(onBridgeEvent as never);

    return () => {
      bridge.unsubscribe(onBridgeEvent as never);
    };
  }, [canGoBack, goBack]);

  const value = useMemo(
    () => ({
      tab,
      stack,
      current,
      setTab,
      openEvent,
      openClassified,
      openIssue,
      openProfile,
      openHelp,
      goBack,
      canGoBack,
      isDetailView,
      isOverlayView,
    }),
    [
      tab,
      stack,
      current,
      setTab,
      openEvent,
      openClassified,
      openIssue,
      openProfile,
      openHelp,
      goBack,
      canGoBack,
      isDetailView,
      isOverlayView,
    ],
  );

  return <VkNavigationContext.Provider value={value}>{children}</VkNavigationContext.Provider>;
}

export function useVkNavigation() {
  const ctx = useContext(VkNavigationContext);
  if (!ctx) throw new Error("useVkNavigation must be used inside VkNavigationProvider");
  return ctx;
}

