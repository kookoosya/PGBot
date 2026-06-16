import bridge from "@vkontakte/vk-bridge";

const VK_APP_ID = Number(import.meta.env.VITE_VK_APP_ID || "0");

export function isVkEnvironment(): boolean {
  if (typeof window === "undefined") return false;
  const params = new URLSearchParams(window.location.search);
  return params.has("vk_app_id") || params.has("vk_user_id") || Boolean((window as Window & { vkBridge?: unknown }).vkBridge);
}

export async function initVkBridge(): Promise<void> {
  if (!isVkEnvironment()) return;
  try {
    await bridge.send("VKWebAppInit");
  } catch {
    // Local dev outside VK iframe
  }
}

export async function getSilentAuthPayload(): Promise<{ silent_token: string; uuid: string }> {
  if (!VK_APP_ID) {
    throw new Error("VITE_VK_APP_ID не задан");
  }
  const result = (await bridge.send(
    "VKWebAppGetSilentToken" as "VKWebAppInit",
    { app_id: VK_APP_ID } as never,
  )) as { token?: string; uuid?: string };
  if (!result?.token || !result?.uuid) {
    throw new Error("VK не вернул silent token");
  }
  return { silent_token: result.token, uuid: result.uuid };
}

export async function getDevSilentAuthPayload(vkUserId = 1001): Promise<{ silent_token: string; uuid: string }> {
  return {
    silent_token: `dev:${vkUserId}`,
    uuid: `dev-${vkUserId}-${Date.now()}`,
  };
}

export async function resolveSilentAuthPayload(): Promise<{ silent_token: string; uuid: string }> {
  if (isVkEnvironment()) {
    if (!VK_APP_ID) {
      throw new Error("VITE_VK_APP_ID не задан — укажите ID мини-приложения");
    }
    return getSilentAuthPayload();
  }
  if (import.meta.env.DEV) {
    return getDevSilentAuthPayload();
  }
  throw new Error("Откройте мини-приложение из ВКонтакте");
}

export function setVkViewportHeight(): void {
  if (!isVkEnvironment()) return;
  bridge.send("VKWebAppResizeWindow", { width: window.innerWidth, height: window.innerHeight }).catch(() => {});
}
