import type { BusinessType, KioskScreenOrientation } from "@/lib/types";
import {
  KIOSK_ACTION_BEHAVIORS,
  KIOSK_CARD_STYLES,
  KIOSK_CATEGORY_STYLES,
  KIOSK_PRODUCT_DISPLAY_STYLES,
  type KioskActionBehavior,
  type KioskCardStyle,
  type KioskCategoryStyle,
  type KioskDisplaySettings,
  type KioskProductDisplayStyle,
} from "@/lib/kiosk/kiosk-business-config";
import { DEFAULT_KIOSK_ACCENT, KIOSK_MULTI_ACCENT, isKioskMultiAccent, normalizeKioskAccent } from "@/lib/kiosk/kiosk-accent";

export const businessTypes: { id: BusinessType; label: string }[] = [
  { id: "restaurant", label: "Restaurant" },
  { id: "cafe", label: "Cafe" },
  { id: "retail", label: "Retail Store" },
  { id: "bakery", label: "Bakery" },
  { id: "pizza", label: "Pizza" },
  { id: "burger", label: "Burger" },
  { id: "grocery", label: "Grocery" },
  { id: "salon", label: "Salon" },
  { id: "ice_cream", label: "Ice Cream" },
  { id: "other", label: "Other" },
];

type KioskTheme = {
  id: string;
  label: string;
  description: string;
  bestUse: string;
  categoryPlacement: "top_category" | "left_category" | "category_gate";
  accent: string;
  mode: "premium_light" | "premium_contrast";
  types: BusinessType[];
};

const allKioskBusinessTypes: BusinessType[] = [
  "restaurant",
  "cafe",
  "retail",
  "bakery",
  "pizza",
  "burger",
  "grocery",
  "salon",
  "ice_cream",
  "other",
];

export const kioskTemplates: KioskTheme[] = [
  {
    id: "top_category",
    label: "Visual Top Menu",
    description: "Image-first categories scroll across the top with a stable product grid and reserved action bar below.",
    bestUse: "visual category browsing",
    categoryPlacement: "top_category",
    accent: "#6D5DFB",
    mode: "premium_light",
    types: allKioskBusinessTypes,
  },
  {
    id: "left_category",
    label: "Side Rail Menu",
    description: "A visual category rail stays on the left while customers browse a stable product grid on the right.",
    bestUse: "large category catalogs",
    categoryPlacement: "left_category",
    accent: "#6D5DFB",
    mode: "premium_light",
    types: allKioskBusinessTypes,
  },
  {
    id: "category_gate",
    label: "Category Gate Menu",
    description: "Customers choose a large image category first, then enter a focused grid containing only that category.",
    bestUse: "category-first shopping",
    categoryPlacement: "category_gate",
    accent: "#6D5DFB",
    mode: "premium_light",
    types: allKioskBusinessTypes,
  },
];

export const legacyKioskTemplateMap: Record<string, string> = {
  chef_picks_portrait: "top_category",
  urban_bites_offer: "category_gate",
  category_strip_pro: "top_category",
  retail_catalog_pro: "left_category",
  checkout_focus: "top_category",
  top_categories: "top_category",
  left_category_rail: "left_category",
  right_category_rail: "left_category",
  photo_hero_menu: "category_gate",
  compact_qsr: "top_category",
  supermarket_grid: "category_gate",
  visual_card_grid: "top_category",
  minimal_list_view: "top_category",
  retail_catalog: "left_category",
  dark_premium: "category_gate",
  category_carousel: "category_gate",
  combo_focus: "top_category",
  guided_category: "category_gate",
  "top-category": "top_category",
  "left-category": "left_category",
  supermarket: "category_gate",
  "category-first": "category_gate",
  "combo-based": "top_category",
  "fast-add": "top_category",
  "category-focus": "category_gate",
  combo_based: "top_category",
  fast_add: "top_category",
  category_focus: "category_gate",
};

export type KioskThemeMode = "premium_light" | "premium_contrast";

export function normalizeKioskTemplateId(id?: string | null) {
  const rawId = id ?? "";
  const templateId = rawId.split(":")[0];
  const normalized = (legacyKioskTemplateMap[templateId] ?? templateId) || "top_category";
  return kioskTemplates.some((template) => template.id === normalized) ? normalized : "top_category";
}

export function parseKioskThemeSelection(id?: string | null, fallbackMode: KioskThemeMode = "premium_contrast") {
  const rawId = id ?? "";
  const [rawTemplateId, rawMode, rawCardStyle, rawCategoryStyle, rawProductDisplayStyle, rawActionBehavior, rawAccentColor] =
    rawId.split(":");
  const mappedTemplateId = legacyKioskTemplateMap[rawTemplateId] ?? rawTemplateId;
  const templateRecognized = kioskTemplates.some((template) => template.id === mappedTemplateId);
  const mode: KioskThemeMode =
    rawMode === "premium_light" || rawMode === "light"
      ? "premium_light"
      : rawMode === "premium_contrast" || rawMode === "dark"
        ? "premium_contrast"
        : fallbackMode;
  return {
    templateId: normalizeKioskTemplateId(rawId),
    templateRecognized,
    mode,
    cardStyle: (KIOSK_CARD_STYLES.includes(rawCardStyle as KioskCardStyle) ? rawCardStyle : "auto") as KioskCardStyle,
    categoryStyle: (rawCategoryStyle === "image_cards"
      ? "picture_card"
      : rawCategoryStyle === "motion_tabs" || rawCategoryStyle === "simple_tabs"
        ? "simple_button"
        : KIOSK_CATEGORY_STYLES.includes(rawCategoryStyle as KioskCategoryStyle)
          ? rawCategoryStyle
          : undefined) as KioskCategoryStyle | undefined,
    productDisplayStyle: (rawProductDisplayStyle === "grid" || rawProductDisplayStyle === "carousel"
      ? "detailed_card"
      : rawProductDisplayStyle === "dense_fast_add_list" || rawProductDisplayStyle === "list"
        ? "simple_item"
        : KIOSK_PRODUCT_DISPLAY_STYLES.includes(rawProductDisplayStyle as KioskProductDisplayStyle)
          ? rawProductDisplayStyle
          : undefined) as KioskProductDisplayStyle | undefined,
    actionBehavior: (KIOSK_ACTION_BEHAVIORS.includes(rawActionBehavior as KioskActionBehavior)
      ? rawActionBehavior
      : "auto") as KioskActionBehavior,
    accentColor: isKioskMultiAccent(rawAccentColor)
      ? KIOSK_MULTI_ACCENT
      : normalizeKioskAccent(rawAccentColor ?? DEFAULT_KIOSK_ACCENT),
  };
}

export function formatKioskThemeSelection(
  id?: string | null,
  mode: KioskThemeMode = "premium_contrast",
  settings?: Partial<Omit<KioskDisplaySettings, "selectedLayout">>
) {
  const templateId = normalizeKioskTemplateId(id);
  if (!settings) return `${templateId}:${mode}`;
  return [
    templateId,
    mode,
    settings.cardStyle ?? "auto",
    settings.categoryStyle ?? "simple_button",
    settings.productDisplayStyle ?? "detailed_card",
    settings.actionBehavior ?? "auto",
    isKioskMultiAccent(settings.accentColor) ? KIOSK_MULTI_ACCENT : normalizeKioskAccent(settings.accentColor),
  ].join(":");
}

export function normalizeKioskScreenOrientation(value?: string | null): KioskScreenOrientation {
  return value === "portrait" ? "portrait" : "landscape";
}


