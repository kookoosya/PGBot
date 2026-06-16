import { createContext, useCallback, useContext, useMemo, useState } from "react";

export type VkTab = "events" | "classifieds" | "issues";

export type VkDetail =
  | { type: "event"; id: number }
  | { type: "classified"; id: number }
  | null;

interface VkNavigationContextValue {
  tab: VkTab;
  detail: VkDetail;
  setTab: (tab: VkTab) => void;
  openEvent: (id: number) => void;
  openClassified: (id: number) => void;
  goBack: () => void;
  isDetailView: boolean;
}

const VkNavigationContext = createContext<VkNavigationContextValue | null>(null);

export function VkNavigationProvider({ children }: { children: React.ReactNode }) {
  const [tab, setTabState] = useState<VkTab>("events");
  const [detail, setDetail] = useState<VkDetail>(null);

  const setTab = useCallback((next: VkTab) => {
    setTabState(next);
    setDetail(null);
  }, []);

  const openEvent = useCallback((id: number) => setDetail({ type: "event", id }), []);
  const openClassified = useCallback((id: number) => setDetail({ type: "classified", id }), []);
  const goBack = useCallback(() => setDetail(null), []);

  const value = useMemo(
    () => ({
      tab,
      detail,
      setTab,
      openEvent,
      openClassified,
      goBack,
      isDetailView: detail !== null,
    }),
    [tab, detail, setTab, openEvent, openClassified, goBack],
  );

  return <VkNavigationContext.Provider value={value}>{children}</VkNavigationContext.Provider>;
}

export function useVkNavigation() {
  const ctx = useContext(VkNavigationContext);
  if (!ctx) throw new Error("useVkNavigation must be used inside VkNavigationProvider");
  return ctx;
}
