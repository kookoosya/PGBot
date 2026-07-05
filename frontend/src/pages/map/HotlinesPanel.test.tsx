/**
 * @vitest-environment jsdom
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HotlinesPanel } from "./HotlinesPanel";
import type { VerifiedPhoneContactsState } from "./useVerifiedPhoneContacts";

const baseContacts: VerifiedPhoneContactsState = {
  loading: false,
  error: false,
  emergencyCount: 5,
  verifiedPlaceCount: 1,
  totalDisplayCount: 6,
  groups: [
    {
      title: "Медицина и аптеки",
      items: [
        {
          id: "place-333",
          icon: "💊",
          name: "Аптека-А",
          phone: "+7 (8112) 60-77-11",
          category: "pharmacy",
          category_label: "Аптека",
          address: "ул. Новоржевская, 25",
          note: "ул. Новоржевская, 25",
          website: null,
          verification_label: null,
        },
      ],
    },
  ],
};

describe("HotlinesPanel", () => {
  it("renders emergency numbers", () => {
    render(<HotlinesPanel compact contacts={baseContacts} />);
    expect(screen.getByText("112")).toBeTruthy();
    expect(screen.getByText("103")).toBeTruthy();
  });

  it("renders verified place phones from API groups", () => {
    const { container } = render(<HotlinesPanel compact contacts={baseContacts} />);
    expect(screen.getAllByText("+7 (8112) 60-77-11").length).toBeGreaterThan(0);
    expect(container.querySelectorAll(".phone-contact-section").length).toBeGreaterThan(1);
  });
});
