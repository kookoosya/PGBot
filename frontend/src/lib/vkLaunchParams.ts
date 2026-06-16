const VK_PARAM_PREFIX = "vk_";

/** Collect VK launch params from search and hash fragments. */
export function readVkLaunchParams(): string {
  if (typeof window === "undefined") return "";
  const search = window.location.search.replace(/^\?/, "");
  const hash = window.location.hash.replace(/^#/, "");
  const combined = [search, hash].filter(Boolean).join("&");
  if (!combined) return "";

  const params = new URLSearchParams(combined);
  const vkPairs: string[] = [];
  params.forEach((value, key) => {
    if (key.startsWith(VK_PARAM_PREFIX) || key === "sign") {
      vkPairs.push(`${key}=${value}`);
    }
  });
  return vkPairs.join("&");
}

export function isVkMiniAppContext(): boolean {
  const raw = readVkLaunchParams();
  return raw.includes("vk_user_id=") || raw.includes("vk_platform=");
}
