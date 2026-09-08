import type { KioskMenu, LiveDeviceContext, Order, Product } from "@/lib/types";
import { ApiError } from "@/lib/api";

export type TestRuntimeApp = "kiosk" | "counter" | "kitchen";
export type TestRuntimeOrder = Record<string, unknown>;

export function testSessionStateMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : "";
  const status = error instanceof ApiError ? error.status : 0;
  if (status >= 500 || /service|network|fetch|timeout/i.test(message)) return "Test application service unavailable. Retry from this application.";
  if (/invalid|expired|revoked|ended/i.test(message)) return "Test session expired. This isolated test environment is no longer active.";
  return "Test session unavailable. Start a test session from Test Device before opening this application.";
}

export function testDeviceContext(menu: KioskMenu, appType: Exclude<TestRuntimeApp, "kiosk">): LiveDeviceContext {
  return {
    business: menu.business,
    device: {
      id: `test-${appType}`,
      business_id: menu.business.id,
      device_id: `test-${appType}`,
      device_type: appType,
      name: `Test ${appType[0].toUpperCase()}${appType.slice(1)}`,
      display_name: `Test ${appType[0].toUpperCase()}${appType.slice(1)}`,
      status: "online",
      location_label: "Isolated test session",
      is_active: true,
    },
    launch_path: `/test/${appType}`,
  };
}

export function testOrder(raw: TestRuntimeOrder, businessId: string): Order {
  const kitchen = (raw.kitchen && typeof raw.kitchen === "object" ? raw.kitchen : {}) as Record<string, unknown>;
  const kitchenStatus = typeof raw.kitchen_status === "string" ? raw.kitchen_status : typeof kitchen.stage === "string" ? kitchen.stage : "pending";
  const status = (raw.counter_state === "handed_over" || kitchenStatus === "completed" ? "completed" : kitchenStatus === "pending_payment" ? "payment_pending" : kitchenStatus) as Order["status"];
  const items = (Array.isArray(raw.items) ? raw.items : []).map((item) => {
    const line = item as TestRuntimeOrder;
    return {
    id: String(line.id),
    order_id: String(raw.id),
    business_id: businessId,
    product_id: typeof line.product_id === "string" ? line.product_id : null,
    product_name: String(line.name || line.product_name || "Item"),
    quantity: Number(line.quantity || 0),
    unit_price: Number(line.unit_price || 0),
    total_price: Number(line.line_total ?? line.total_price ?? 0),
    notes: typeof line.notes === "string" ? line.notes : null,
    customizations: (line.modifiers || line.customizations || []) as Record<string, unknown>[],
    completed_quantity: Number(line.completed_quantity || 0),
  };
  });
  return {
    id: String(raw.id),
    business_id: businessId,
    location_id: typeof raw.location_id === "string" ? raw.location_id : null,
    order_number: typeof raw.order_number === "number" ? raw.order_number : null,
    public_token: typeof raw.public_token === "string" ? raw.public_token : `TEST-${String(raw.id).slice(0, 8).toUpperCase()}`,
    status,
    order_type: raw.order_type === "dine_in" ? "dine_in" : "takeaway",
    table_label: typeof raw.table_label === "string" ? raw.table_label : null,
    subtotal: Number(raw.subtotal || 0),
    tax_amount: Number(raw.tax_amount || 0),
    discount_amount: Number(raw.discount_amount || 0),
    total_amount: Number(raw.total_amount || 0),
    payment_status: typeof raw.payment_status === "string" ? raw.payment_status : "awaiting_payment",
    payment_method: typeof raw.payment_method === "string" ? raw.payment_method : "simulated_test",
    source: typeof raw.source === "string" ? raw.source : "test",
    notes: typeof raw.notes === "string" ? raw.notes : null,
    placed_at: typeof raw.created_at === "string" ? raw.created_at : typeof raw.placed_at === "string" ? raw.placed_at : new Date().toISOString(),
    prep_started_at: typeof raw.preparing_started_at === "string" ? raw.preparing_started_at : typeof kitchen.preparing_started_at === "string" ? kitchen.preparing_started_at : null,
    ready_at: typeof raw.ready_at === "string" ? raw.ready_at : typeof kitchen.ready_at === "string" ? kitchen.ready_at : null,
    completed_at: typeof raw.completed_at === "string" ? raw.completed_at : typeof raw.handed_over_at === "string" ? raw.handed_over_at : null,
    order_items: items,
    kitchen: { ...kitchen, delayed: kitchen.delayed ?? kitchen.is_delayed ?? false },
  } as Order;
}

export function testProducts(products: Product[]): Product[] {
  return products.map((product) => {
    const raw = product as Product & { product_id?: string };
    return {
      ...product,
      id: product.id || raw.product_id || "",
      is_available: product.is_available !== false,
    };
  });
}
