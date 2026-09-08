import { expect, test } from "@playwright/test";
import { resolveHomeMode } from "../src/components/dashboard/home-state";
import type { KioskSetupOverview, Product } from "../src/lib/types";
import type { Business } from "../src/services/api";

const setup = { status: { businessComplete: true, menuComplete: true, kioskSettingsComplete: true, welcomeScreenComplete: true } } as KioskSetupOverview;
const business = { kiosk_order_settings: { default_payment_method: "counter" }, payment_summary: { enabled_methods: [] } } as unknown as Business;
const menu = [{ is_available: true, category_id: "category" }] as Product[];

test("Home mode uses setup, first-order, then active precedence", () => {
  expect(resolveHomeMode(business, { ...setup, status: { ...setup.status, menuComplete: false } }, menu, 12)).toBe("setup");
  expect(resolveHomeMode(business, setup, menu, 0)).toBe("first_order");
  expect(resolveHomeMode(business, setup, menu, 1)).toBe("active");
});
