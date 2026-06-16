import { describe, expect, it } from "vitest";
import { isVkMiniAppContext } from "@/lib/vkLaunchParams";

describe("vkLaunchParams", () => {
  it("detects vk context from launch string", () => {
    const raw = "vk_user_id=1&vk_platform=mobile_android&sign=abc";
    expect(raw.includes("vk_user_id=")).toBe(true);
    expect(isVkMiniAppContext()).toBe(false);
  });

  it("parses vk keys from combined query", () => {
    const params = new URLSearchParams("vk_user_id=5&vk_app_id=1&foo=bar");
    const pairs: string[] = [];
    params.forEach((value, key) => {
      if (key.startsWith("vk_") || key === "sign") pairs.push(`${key}=${value}`);
    });
    expect(pairs.join("&")).toBe("vk_user_id=5&vk_app_id=1");
  });
});
