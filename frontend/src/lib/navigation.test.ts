import { describe, expect, it } from "vitest";
import type { User } from "@/lib/api/types/auth";
import {
  MAIN_SECTIONS,
  PORTAL_NAV_ITEMS,
  getUserHomeLabel,
  getUserHomePath,
} from "./navigation";

const user = (role: User["role"]): User =>
  ({
    id: 1,
    username: "u",
    role,
    full_name: "Test",
  }) as User;

describe("navigation", () => {
  it("routes anonymous users to cabinet login", () => {
    expect(getUserHomePath(null)).toBe("/cabinet/login");
    expect(getUserHomeLabel(null)).toBe("Вход");
  });

  it("routes residents to cabinet", () => {
    expect(getUserHomePath(user("resident"))).toBe("/cabinet");
    expect(getUserHomeLabel(user("resident"))).toBe("Личный кабинет");
  });

  it("routes officials to official portal", () => {
    expect(getUserHomePath(user("administration"))).toBe("/official");
    expect(getUserHomeLabel(user("moderator"))).toBe("Портал служб");
  });

  it("routes service providers to services cabinet", () => {
    expect(getUserHomePath(user("service_provider"))).toBe("/services/cabinet");
    expect(getUserHomeLabel(user("service_provider"))).toBe("Кабинет мастера");
  });

  it("lists main portal sections with map and events", () => {
    const paths = MAIN_SECTIONS.map((s) => s.to);
    expect(paths).toContain("/map");
    expect(paths).toContain("/events");
    expect(PORTAL_NAV_ITEMS.some((s) => s.to === "/cabinet")).toBe(true);
  });
});
