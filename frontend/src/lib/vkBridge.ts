import bridge from "@vkontakte/vk-bridge";
import { isVkMiniAppContext, readVkLaunchParams } from "./vkLaunchParams";

/** True when running inside the VK native webview (vk-bridge). */
export function isVkBridgeWebView(): boolean {
  try {
    return bridge.isWebView();
  } catch {
    return false;
  }
}

/** VK Mini App context: bridge webview or signed launch params in URL. */
export function isVkMiniAppRuntime(): boolean {
  return isVkBridgeWebView() || isVkMiniAppContext();
}

function launchParamsToQuery(params: Record<string, unknown>): string {
  const pairs: string[] = [];
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === "") continue;
    if (key.startsWith("vk_") || key === "sign") {
      pairs.push(`${key}=${encodeURIComponent(String(value))}`);
    }
  }
  return pairs.join("&");
}

/** Read launch params from vk-bridge, falling back to URL fragments. */
export async function readVkLaunchParamsAsync(): Promise<string> {
  if (isVkBridgeWebView()) {
    try {
      const data = await bridge.send("VKWebAppGetLaunchParams");
      if (data && typeof data === "object") {
        const query = launchParamsToQuery(data as Record<string, unknown>);
        if (query) return query;
      }
    } catch {
      // Older clients may not support GetLaunchParams — use URL.
    }
  }
  return readVkLaunchParams();
}

/** Initialize vk-bridge and apply compact Mini App chrome. */
export async function initVkBridge(): Promise<void> {
  if (!isVkBridgeWebView()) return;
  try {
    await bridge.send("VKWebAppInit");
    await bridge.send("VKWebAppSetViewSettings", {
      status_bar_style: "light",
      action_bar_color: "#2d4a2b",
      navigation_bar_color: "#faf8f4",
    });
  } catch {
    // Preview outside VK — ignore.
  }
}
