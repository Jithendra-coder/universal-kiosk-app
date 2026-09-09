import type { BusinessType } from "@/lib/types";
import { DEFAULT_KIOSK_ACCENT, normalizeKioskAccent } from "@/lib/kiosk/kiosk-accent";

export type KioskLayoutId = "top_category" | "left_category" | "category_gate";
export type KioskFlowType = "cart" | "booking";
export type KioskItemNoun = "item" | "product" | "service";
export type KioskCardStyle = "auto" | "compact" | "detailed" | "image_focused" | "fast_add";
export type KioskCategoryStyle = "simple_button" | "picture_card" | "image_cards" | "motion_tabs";
export type KioskProductDisplayStyle = "simple_item" | "detailed_card" | "grid" | "dense_fast_add_list";
export type KioskActionBehavior =
  | "auto"
  | "direct_add"
  | "customize_first"
  | "variant_select"
  | "quantity_stepper"
  | "booking";

export type KioskDisplaySettings = {
  selectedLayout: KioskLayoutId;
  cardStyle: KioskCardStyle;
  categoryStyle: KioskCategoryStyle;
  productDisplayStyle: KioskProductDisplayStyle;
  actionBehavior: KioskActionBehavior;
  accentColor: string;
};

export type KioskBusinessConfig = {
  type: BusinessType;
  allowedLayouts: KioskLayoutId[];
  defaultLayout: KioskLayoutId;
  flowType: KioskFlowType;
  itemNoun: KioskItemNoun;
  itemNounPlural: string;
  startLabel: string;
  secondaryStartLabel: string;
  checkoutLabel: string;
  emptyLabel: string;
  showPrepTime: boolean;
  showDietaryType: boolean;
  showStock: boolean;
  showUnit: boolean;
  showBrand: boolean;
  showDuration: boolean;
  showVariants: boolean;
  showAddons: boolean;
  showCombos: boolean;
  defaultCardStyle: Exclude<KioskCardStyle, "auto">;
  defaultCategoryStyle: KioskCategoryStyle;
  defaultProductDisplayStyle: KioskProductDisplayStyle;
  defaultActionBehavior: Exclude<KioskActionBehavior, "auto">;
};

export const KIOSK_LAYOUT_IDS: KioskLayoutId[] = ["top_category", "left_category", "category_gate"];
export const KIOSK_CARD_STYLES: KioskCardStyle[] = ["auto", "compact", "detailed", "image_focused", "fast_add"];
export const KIOSK_CATEGORY_STYLES: KioskCategoryStyle[] = ["simple_button", "picture_card", "image_cards", "motion_tabs"];
export const KIOSK_PRODUCT_DISPLAY_STYLES: KioskProductDisplayStyle[] = ["simple_item", "detailed_card", "grid", "dense_fast_add_list"];
export const KIOSK_ACTION_BEHAVIORS: KioskActionBehavior[] = [
  "auto",
  "direct_add",
  "customize_first",
  "variant_select",
  "quantity_stepper",
  "booking",
];

const foodBase: Omit<KioskBusinessConfig, "type"> = {
  allowedLayouts: KIOSK_LAYOUT_IDS,
  flowType: "cart",
  itemNoun: "item",
  itemNounPlural: "items",
  startLabel: "Start Your Order",
  secondaryStartLabel: "View Menu",
  checkoutLabel: "Checkout",
  emptyLabel: "No items found",
  showPrepTime: true,
  showDietaryType: true,
  showStock: false,
  showUnit: false,
  showBrand: false,
  showDuration: false,
  showVariants: true,
  showAddons: true,
  showCombos: true,
  defaultLayout: "top_category",
  defaultCardStyle: "detailed",
  defaultCategoryStyle: "simple_button",
  defaultProductDisplayStyle: "detailed_card",
  defaultActionBehavior: "direct_add",
};

const overrides: Partial<Record<BusinessType, Partial<KioskBusinessConfig>>> = {
  cafe: { defaultCardStyle: "compact" },
  pizza: { defaultActionBehavior: "customize_first" },
  burger: { defaultActionBehavior: "customize_first" },
  bakery: { defaultLayout: "category_gate", showPrepTime: false, showStock: true, showUnit: true, defaultCardStyle: "image_focused" },
  ice_cream: { showPrepTime: false, defaultCardStyle: "image_focused", defaultActionBehavior: "customize_first" },
  grocery: {
    defaultLayout: "category_gate", itemNoun: "product", itemNounPlural: "products", startLabel: "Start Shopping",
    secondaryStartLabel: "Browse Products", showPrepTime: false, showDietaryType: false, showStock: true, showUnit: true,
    showBrand: true, showAddons: false, showCombos: false, defaultCardStyle: "compact", defaultActionBehavior: "quantity_stepper",
  },
  retail: {
    defaultLayout: "category_gate", itemNoun: "product", itemNounPlural: "products", startLabel: "Start Shopping",
    secondaryStartLabel: "Browse Products", showPrepTime: false, showDietaryType: false, showStock: true,
    showBrand: true, showAddons: false, showCombos: false, defaultCardStyle: "compact", defaultActionBehavior: "quantity_stepper",
  },
  salon: {
    defaultLayout: "category_gate", flowType: "booking", itemNoun: "service", itemNounPlural: "services",
    startLabel: "Book a Service", secondaryStartLabel: "Browse Services", checkoutLabel: "Confirm Booking",
    emptyLabel: "No services found", showPrepTime: false, showDietaryType: false, showDuration: true, defaultActionBehavior: "booking",
  },
  other: { showPrepTime: false, showDietaryType: false, showCombos: false, defaultCardStyle: "compact" },
};

const configCache = new Map<string, KioskBusinessConfig>();

export async function fetchServerKioskConfig(type: BusinessType): Promise<{ config: KioskBusinessConfig; displaySettings: KioskDisplaySettings } | null> {
  try {
    const res = await fetch(`/api/kiosk/config/${type}`);
    if (res.ok) {
      const data = await res.json();
      if (data?.config) {
        configCache.set(type, data.config);
      }
      return data;
    }
  } catch {}
  return null;
}

export function kioskBusinessConfig(type?: BusinessType | null): KioskBusinessConfig {
  const key = type ?? "other";
  if (configCache.has(key)) return configCache.get(key)!;
  const resolved: KioskBusinessConfig = {
    ...foodBase,
    ...(overrides[key] || {}),
    type: key,
  };
  configCache.set(key, resolved);
  return resolved;
}

export function resolveKioskDisplaySettings(
  type: BusinessType,
  settings?: Partial<KioskDisplaySettings> | null
): KioskDisplaySettings {
  const config = kioskBusinessConfig(type);
  const selectedLayout = KIOSK_LAYOUT_IDS.includes(settings?.selectedLayout as KioskLayoutId)
    ? (settings?.selectedLayout as KioskLayoutId)
    : config.defaultLayout;
  const cardStyle = KIOSK_CARD_STYLES.includes(settings?.cardStyle as KioskCardStyle)
    ? (settings?.cardStyle as KioskCardStyle)
    : "auto";
  const rawCategoryStyle = settings?.categoryStyle;
  const categoryStyle =
    rawCategoryStyle === "image_cards"
      ? "picture_card"
      : rawCategoryStyle === "motion_tabs"
        ? "simple_button"
        : KIOSK_CATEGORY_STYLES.includes(rawCategoryStyle as KioskCategoryStyle)
          ? (rawCategoryStyle as KioskCategoryStyle)
          : config.defaultCategoryStyle;
  const productDisplayStyle = KIOSK_PRODUCT_DISPLAY_STYLES.includes(
    settings?.productDisplayStyle as KioskProductDisplayStyle
  )
    ? settings?.productDisplayStyle === "grid"
      ? "detailed_card"
      : settings?.productDisplayStyle === "dense_fast_add_list"
        ? "simple_item"
        : (settings?.productDisplayStyle as KioskProductDisplayStyle)
    : config.defaultProductDisplayStyle;
  let actionBehavior = KIOSK_ACTION_BEHAVIORS.includes(settings?.actionBehavior as KioskActionBehavior)
    ? (settings?.actionBehavior as KioskActionBehavior)
    : "auto";

  if (config.flowType === "booking") actionBehavior = "booking";
  if (actionBehavior === "booking" && config.flowType !== "booking") actionBehavior = "auto";
  if (!isKioskActionBehaviorAllowed(type, actionBehavior)) actionBehavior = "auto";

  return {
    selectedLayout,
    cardStyle,
    categoryStyle,
    productDisplayStyle,
    actionBehavior,
    accentColor: normalizeKioskAccent(settings?.accentColor ?? DEFAULT_KIOSK_ACCENT),
  };
}

export function effectiveKioskCardStyle(type: BusinessType, style: KioskCardStyle) {
  return style === "auto" ? kioskBusinessConfig(type).defaultCardStyle : style;
}

export function isKioskActionBehaviorAllowed(type: BusinessType, behavior: KioskActionBehavior) {
  const config = kioskBusinessConfig(type);
  if (behavior === "auto") return true;
  if (config.flowType === "booking") return behavior === "booking";
  if (behavior === "booking") return false;
  if (behavior === "quantity_stepper") return type === "grocery" || type === "retail";
  if (behavior === "variant_select") return config.showVariants;
  if (behavior === "customize_first") return config.showVariants || config.showAddons;
  return behavior === "direct_add";
}
