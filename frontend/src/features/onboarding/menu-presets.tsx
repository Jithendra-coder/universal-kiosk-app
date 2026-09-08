"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { KioskLayoutId } from "@/lib/kiosk/kiosk-business-config";
import type {
  Business,
  BusinessType,
  Category,
  ItemType,
  KioskScreenOrientation,
  OrderType,
  Product,
} from "@/lib/types";
import type { Business as OnboardingBusiness } from "@/services/api";

export type MenuPreset = {
  id: string;
  name: string;
  imagePath: string;
  category: string;
  foodType?: "veg" | "non-veg";
};

export type MenuPresetExperienceState = {
  catalogKey: string;
  visiblePresetIds: string[];
  selectedPresetIds: string[];
  rotationCursor: number;
};

type AssetType = "bakery" | "burger" | "cafe" | "grocery" | "ice-cream" | "other" | "pizza" | "restaurant" | "retail-store" | "salon";
type PresetContextValue = MenuPresetExperienceState & {
  configure: (key: string, presetIds: string[]) => void;
  toggle: (id: string) => void;
  refresh: (catalogIds: string[]) => void;
};

const files: Record<AssetType, Record<string, string[]>> = {
  bakery: {
    "set-01": words("cheese-danish eclair cream-puff swiss-roll red-velvet-cake sponge-cake cheesecake-cup chocolate-truffle shortbread-biscuit pretzel garlic-bread-loaf brioche scone palmier custard-tart"),
    "set-02": words("bread-loaf croissant cupcake chocolate-cake doughnut muffin cookies cinnamon-roll baguette puff-pastry fruit-tart brownie bread-bun macarons fruit-pie"),
  },
  burger: {
    "set-01": words("fish-burger spicy-chicken-burger bacon-burger mushroom-burger paneer-burger mini-sliders loaded-fries cheese-fries potato-wedges mozzarella-sticks chicken-tenders corn-dog coleslaw lemonade chocolate-brownie"),
    "set-02": words("classic-burger cheeseburger chicken-burger double-burger vegetable-burger french-fries onion-rings chicken-nuggets hot-dog grilled-wrap fried-chicken milkshake soft-drink dipping-sauce ice-cream-sundae"),
  },
  cafe: {
    "set-01": words("cold-brew hot-chocolate green-tea lemon-tea masala-chai club-sandwich garlic-toast pancakes waffles bagel apple-pie chocolate-tart banana-bread fruit-bowl nachos"),
    "set-02": words("cappuccino latte espresso iced-coffee mocha tea croissant grilled-sandwich muffin cheesecake brownie cookies doughnut vegetable-wrap french-fries"),
  },
  grocery: {
    "set-01": words("oranges grapes watermelon cucumber bell-peppers spinach cheese butter flour sugar salt lentils pasta-pack biscuits dishwashing-liquid"),
    "set-02": words("apples bananas tomatoes potatoes onions carrots milk eggs bread rice cooking-oil cereal orange-juice yoghurt detergent"),
  },
  "ice-cream": {
    "set-01": words("vanilla-ice-cream chocolate-ice-cream strawberry-ice-cream mango-ice-cream butterscotch-ice-cream black-currant-ice-cream pistachio-ice-cream cookies-and-cream-ice-cream kulfi ice-cream-sundae ice-cream-cone ice-cream-cup brownie-with-ice-cream banana-split milkshake"),
    "set-02": words("vanilla-ice-cream chocolate-ice-cream strawberry-ice-cream mango-ice-cream mint-ice-cream waffle-cone ice-cream-sundae ice-cream-sandwich popsicle soft-serve chocolate-syrup-ice-cream sprinkle-ice-cream waffle-bowl banana-split milkshake"),
  },
  other: {
    "set-01": words("burger pizza sandwich ice-cream coffee t-shirt shoes handbag wristwatch headphones haircut beard-trim head-massage gift-box flower-bouquet"),
  },
  pizza: {
    "set-01": words("bbq-chicken-pizza hawaiian-pizza four-cheese-pizza paneer-tikka-pizza spicy-sausage-pizza seafood-pizza spinach-pizza corn-pizza olive-pizza stuffed-crust-pizza cheese-balls mozzarella-sticks potato-wedges caesar-salad chocolate-lava-cake"),
    "set-02": words("margherita-pizza pepperoni-pizza vegetable-pizza cheese-pizza chicken-pizza mushroom-pizza garlic-bread breadsticks pizza-slice calzone pasta chicken-wings french-fries soft-drink dipping-sauce"),
  },
  restaurant: {
    "set-01": words("chicken-curry mutton-curry prawn-fry chicken-kebab chilli-chicken gobi-manchurian dal-tadka jeera-rice chapati paratha pulao chicken-soup vegetable-cutlet spring-roll gulab-jamun"),
    "set-02": words("chicken-biryani grilled-chicken butter-naan paneer-curry vegetable-fried-rice noodles masala-dosa idli samosa tandoori-chicken fish-curry vegetarian-thali pasta vegetable-soup mixed-salad"),
  },
  "retail-store": {
    "set-01": words("formal-shirt jacket dress sandals slippers belt cap bracelet necklace smartphone-case bluetooth-speaker umbrella cushion wall-clock shopping-basket"),
    "set-02": words("t-shirt jeans sneakers handbag wristwatch sunglasses perfume headphones backpack wallet water-bottle toy notebook table-lamp coffee-mug"),
  },
  salon: {
    "set-01": words("haircut beard-trim child-haircut hair-wash hair-styling hair-coloring facial cleanup manicure pedicure head-massage hair-spa threading waxing bridal-makeup"),
    "set-02": words("mens-haircut womens-haircut child-haircut beard-trim clean-shave hair-colouring hair-straightening hair-styling facial face-cleanup head-massage hair-spa manicure pedicure body-massage"),
  },
};

export const ALL_MENU_PRESETS: MenuPreset[] = Object.entries(files).flatMap(([type, sets]) => {
  const seen = new Set<string>();
  return Object.entries(sets).flatMap(([set, names]) => names.flatMap((slug, index) => {
    const duplicateKey = slug.replace("colouring", "coloring");
    if (seen.has(duplicateKey)) return [];
    seen.add(duplicateKey);
    return [{
      id: `${type}-${duplicateKey}`,
      name: polishedName(slug),
      imagePath: `/onboarding-menu/${type}/${set}/${String(index + 1).padStart(2, "0")}-${slug}.jpg`,
      category: categoryFor(type as AssetType, slug),
      foodType: foodTypeFor(type as AssetType, slug),
    }];
  }));
});

export function getMenuPresetsForBusinessType({
  businessType,
  businessDescription,
  allPresets,
}: {
  businessType: string;
  businessDescription?: string | null;
  allPresets: MenuPreset[];
}) {
  const resolved = resolveAssetType(businessType, businessDescription);
  return allPresets.filter((preset) => preset.id.startsWith(`${resolved}-`));
}

export function refreshMenuPresetState(state: MenuPresetExperienceState, catalogIds: string[]): MenuPresetExperienceState {
  const visible = state.visiblePresetIds.slice(0, 15);
  const selected = new Set(state.selectedPresetIds);
  const replaceable = visible.flatMap((id, index) => selected.has(id) ? [] : [index]);
  const replacementCount = Math.ceil(replaceable.length / 2);
  const blocked = new Set([...visible, ...selected]);
  const replacements: string[] = [];
  let scanned = 0;
  let cursor = state.rotationCursor % Math.max(1, catalogIds.length);

  while (replacements.length < replacementCount && scanned < catalogIds.length) {
    const id = catalogIds[cursor];
    cursor = (cursor + 1) % catalogIds.length;
    scanned += 1;
    if (!blocked.has(id)) {
      blocked.add(id);
      replacements.push(id);
    }
  }
  replacements.forEach((id, index) => { visible[replaceable[index]] = id; });
  return { ...state, visiblePresetIds: visible, rotationCursor: cursor };
}

export function createOnboardingKioskExperience({
  business,
  presets,
  layout,
  orientation = "portrait",
}: {
  business: OnboardingBusiness;
  presets: MenuPreset[];
  layout?: KioskLayoutId;
  orientation?: KioskScreenOrientation;
}): { business: Business; categories: Category[]; products: Product[] } {
  const businessType = normalizeBusinessType(business.type);
  const businessId = business.id;
  const categories = [...new Set(presets.map((preset) => preset.category))].map((name, sort_order) => ({
    id: `preset-category-${slugify(name)}`,
    business_id: businessId,
    name,
    description: null,
    image_path: presets.find((preset) => preset.category === name)?.imagePath ?? null,
    is_active: true,
    sort_order,
  }));
  const categoryIds = new Map(categories.map((category) => [category.name, category.id]));
  const products: Product[] = presets.map((preset, sort_order) => ({
    id: preset.id,
    business_id: businessId,
    category_id: categoryIds.get(preset.category) || null,
    name: preset.name,
    description: presetDescription(preset, businessType),
    sku: null,
    item_type: presetItemType(preset, businessType),
    price: 99 + (sort_order % 6) * 25,
    discount_type: "none",
    discount_value: 0,
    discount_label: null,
    primary_image_path: preset.imagePath,
    is_available: true,
    is_featured: sort_order < 2,
    track_stock: false,
    stock_quantity: null,
    daily_limit: null,
    sold_today: 0,
    original_price: null,
    display_badge: sort_order < 2 ? "Popular" : null,
    tags: sort_order < 2 ? ["popular"] : [],
    menu_status: "shown",
    sort_order,
    availability_type: "always",
    available_days: [],
    modifier_groups: [],
    metadata: {
      onboarding_preset: true,
      tags: sort_order < 2 ? ["popular"] : [],
    },
  }));
  const raw = business as unknown as Partial<Business>;
  const welcome = business.welcome_screen;
  const selectedLayout = layout ?? legacyLayoutId(business.kiosk_layout_id);
  const currentThemeParts = String(raw.kiosk_theme || "").split(":");
  const kioskTheme = [selectedLayout, ...currentThemeParts.slice(1)].filter(Boolean).join(":") || `${selectedLayout}:premium_light`;
  const orderModes = validOrderModes(business.order_modes);

  return {
    business: {
      id: businessId,
      owner_id: raw.owner_id || "onboarding-preview",
      name: business.name,
      slug: business.slug,
      type: businessType,
      tagline: business.tagline || welcome?.supporting_text || null,
      business_subtype: business.business_subtype || null,
      contact_phone: business.contact_phone || null,
      logo_path: business.logo_path || null,
      logo_shape: raw.logo_shape || "circle",
      logo_scale: raw.logo_scale ?? 1,
      logo_position_x: raw.logo_position_x ?? 50,
      logo_position_y: raw.logo_position_y ?? 50,
      brand_color: business.brand_color || "#0b57f0",
      kiosk_theme: kioskTheme,
      kiosk_layout: selectedLayout,
      kiosk_screen_orientation: orientation,
      kiosk_screen_size: raw.kiosk_screen_size || (orientation === "portrait" ? "1080x1920" : "1920x1080"),
      kiosk_cart_mode: raw.kiosk_cart_mode || "drawer",
      kiosk_start_screen_enabled: welcome?.enabled ?? raw.kiosk_start_screen_enabled ?? true,
      kiosk_start_text_position: welcome?.text_position || raw.kiosk_start_text_position || "middle",
      kiosk_touch_to_start: welcome?.touch_anywhere_to_start ?? raw.kiosk_touch_to_start ?? false,
      kiosk_start_screen_settings: {
        ...raw.kiosk_start_screen_settings,
        configured: true,
        welcome_text: welcome?.heading || raw.kiosk_start_screen_settings?.welcome_text || `Welcome to ${business.name}`,
        instruction_text: welcome?.instruction_text || raw.kiosk_start_screen_settings?.instruction_text || "Tap start when you are ready.",
      },
      kiosk_lock_settings: { ...raw.kiosk_lock_settings, enabled: false },
      kiosk_order_settings: {
        ...raw.kiosk_order_settings,
        ...business.kiosk_order_settings,
        checkout_enabled: true,
        checkout_mode: "basic",
        public_online_ordering_enabled: false,
        require_customer_name: false,
        require_customer_phone: false,
        allow_customer_notes: true,
        show_confirmation: true,
      },
      display_show_tagline: raw.display_show_tagline ?? true,
      display_show_category_images: raw.display_show_category_images ?? true,
      display_show_item_descriptions: raw.display_show_item_descriptions ?? true,
      display_show_prices: raw.display_show_prices ?? true,
      display_show_unavailable: false,
      idle_timeout_seconds: business.idle_timeout_seconds || 60,
      default_language: raw.default_language || "en",
      sound_effects_enabled: false,
      order_reset_seconds: business.order_reset_seconds || 5,
      offer_enabled: raw.offer_enabled ?? true,
      offer_title: raw.offer_title || welcome?.heading || `Welcome to ${business.name}`,
      offer_subtitle: raw.offer_subtitle || welcome?.supporting_text || welcome?.instruction_text || null,
      offer_badge: raw.offer_badge || null,
      offer_cta: raw.offer_cta || welcome?.start_button_text || "Start",
      offer_image_path: raw.offer_image_path || presets[0]?.imagePath || null,
      offer_background: raw.offer_background || business.brand_color || "#0b57f0",
      currency_code: raw.currency_code || "INR",
      currency_symbol: business.currency_symbol || "₹",
      tax_percent: Number(business.tax_percent || 0),
      address_line1: business.address_line1 || null,
      city: business.city || null,
      state: business.state || null,
      postal_code: business.postal_code || null,
      country: raw.country || "India",
      timezone: raw.timezone || "Asia/Kolkata",
      opening_time: raw.opening_time || null,
      closing_time: raw.closing_time || null,
      order_modes: orderModes,
      store_schedule: raw.store_schedule,
      receipt_settings: raw.receipt_settings,
      payment_summary: {
        ...raw.payment_summary,
        enabled_methods: ["pay_at_counter"],
        default_payment_method: "pay_at_counter",
      },
      onboarding_step: business.onboarding_step || 3,
      onboarding_completed: business.onboarding_completed || false,
      is_active: true,
    },
    categories,
    products,
  };
}

const PresetContext = createContext<PresetContextValue | null>(null);

export function MenuPresetExperienceProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<MenuPresetExperienceState>({
    catalogKey: "",
    visiblePresetIds: [],
    selectedPresetIds: [],
    rotationCursor: 15,
  });
  const configure = useCallback((key: string, presetIds: string[]) => setState((current) => current.catalogKey === key ? current : ({
    catalogKey: key,
    visiblePresetIds: presetIds.slice(0, 15),
    selectedPresetIds: [],
    rotationCursor: Math.min(15, presetIds.length),
  })), []);
  const toggle = useCallback((id: string) => setState((current) => ({
    ...current,
    selectedPresetIds: current.selectedPresetIds.includes(id)
      ? current.selectedPresetIds.filter((selectedId) => selectedId !== id)
      : [...current.selectedPresetIds, id],
  })), []);
  const refresh = useCallback((catalogIds: string[]) => setState((current) => refreshMenuPresetState(current, catalogIds)), []);
  const value = useMemo(() => ({ ...state, configure, toggle, refresh }), [configure, refresh, state, toggle]);
  return <PresetContext.Provider value={value}>{children}</PresetContext.Provider>;
}

export function useMenuPresetExperience() {
  const value = useContext(PresetContext);
  if (!value) throw new Error("useMenuPresetExperience must be used inside MenuPresetExperienceProvider.");
  return value;
}

function words(value: string) {
  return value.split(" ");
}

function polishedName(slug: string) {
  const names: Record<string, string> = {
    bbq: "BBQ", idli: "Idli", gobi: "Gobi", jeera: "Jeera", kulfi: "Kulfi",
    mens: "Men's", womens: "Women's", t: "T",
  };
  return slug.split("-").map((word) => names[word] || word.charAt(0).toUpperCase() + word.slice(1)).join(" ").replace(/^T Shirt$/, "T-Shirt");
}

function foodTypeFor(type: AssetType, slug: string): MenuPreset["foodType"] {
  if (type === "retail-store" || type === "salon") return undefined;
  if (type === "other" && !/(burger|pizza|sandwich|ice-cream|coffee)/.test(slug)) return undefined;
  if (type === "grocery" && /(dishwashing|detergent)/.test(slug)) return undefined;
  return /(chicken|mutton|prawn|fish|bacon|sausage|seafood|pepperoni|hawaiian|egg|classic-burger|cheeseburger|double-burger|hot-dog|corn-dog|fried-chicken)/.test(slug) ? "non-veg" : "veg";
}

function categoryFor(type: AssetType, slug: string) {
  if (type === "salon") {
    if (/(manicure|pedicure)/.test(slug)) return "Nail Care";
    if (/(facial|cleanup|threading|waxing|makeup)/.test(slug)) return "Skin & Beauty";
    if (/(massage|spa)/.test(slug)) return "Wellness";
    return "Hair & Grooming";
  }
  if (type === "retail-store") {
    if (/(shirt|jacket|dress|jeans)/.test(slug)) return "Clothing";
    if (/(sandals|slippers|sneakers)/.test(slug)) return "Footwear";
    if (/(case|speaker|headphones)/.test(slug)) return "Electronics";
    if (/(cushion|clock|lamp|mug|bottle|umbrella)/.test(slug)) return "Home & Lifestyle";
    return "Accessories";
  }
  if (type === "grocery") {
    if (/(apple|banana|orange|grape|watermelon|tomato|potato|onion|carrot|cucumber|pepper|spinach)/.test(slug)) return "Fresh Produce";
    if (/(milk|egg|cheese|butter|yoghurt)/.test(slug)) return "Dairy & Eggs";
    if (/(dishwashing|detergent)/.test(slug)) return "Household";
    return "Pantry";
  }
  if (type === "bakery") {
    if (/(bread|loaf|brioche|baguette|bun|pretzel)/.test(slug)) return "Breads";
    if (/(cake|cheesecake|truffle|brownie)/.test(slug)) return "Cakes";
    if (/(biscuit|cookies|shortbread)/.test(slug)) return "Biscuits";
    return "Pastries";
  }
  if (type === "cafe") {
    if (/(coffee|brew|chocolate|tea|chai|cappuccino|latte|espresso|mocha)/.test(slug)) return "Beverages";
    if (/(pie|tart|cake|brownie|cookies|doughnut|muffin)/.test(slug)) return "Desserts";
    return "Cafe Bites";
  }
  if (type === "ice-cream") return /(sundae|split|brownie)/.test(slug) ? "Sundaes" : /(cone|cup|bowl|sandwich|popsicle|serve)/.test(slug) ? "Ice Cream Treats" : /(milkshake)/.test(slug) ? "Shakes" : "Scoop Flavours";
  if (type === "pizza") return slug.includes("pizza") ? "Pizzas" : /(drink)/.test(slug) ? "Drinks" : /(cake)/.test(slug) ? "Desserts" : "Sides";
  if (type === "burger") return slug.includes("burger") || slug.includes("slider") ? "Burgers" : /(lemonade|drink|milkshake)/.test(slug) ? "Drinks" : /(brownie|sundae)/.test(slug) ? "Desserts" : "Sides";
  if (type === "restaurant") return /(rice|chapati|paratha|pulao|naan|biryani)/.test(slug) ? "Rice & Breads" : /(jamun)/.test(slug) ? "Desserts" : /(kebab|fry|cutlet|roll|samosa)/.test(slug) ? "Starters" : "Main Course";
  if (type === "other") return /(burger|pizza|sandwich|ice-cream|coffee)/.test(slug) ? "Food & Drinks" : /(haircut|trim|massage)/.test(slug) ? "Services" : "Products";
  return "Menu";
}

function resolveAssetType(businessType: string, description?: string | null): AssetType {
  const normalized = businessType === "retail" ? "retail-store" : businessType === "ice_cream" ? "ice-cream" : businessType;
  if (normalized !== "other" && normalized in files) return normalized as AssetType;
  const value = (description || "").toLowerCase();
  if (/(salon|hair|beauty|spa|barber)/.test(value)) return "salon";
  if (/(bakery|cake|bread|pastry)/.test(value)) return "bakery";
  if (/(pizza)/.test(value)) return "pizza";
  if (/(burger|fast food)/.test(value)) return "burger";
  if (/(cafe|coffee|tea)/.test(value)) return "cafe";
  if (/(restaurant|food|dining)/.test(value)) return "restaurant";
  if (/(grocery|supermarket|food store)/.test(value)) return "grocery";
  if (/(ice cream|dessert)/.test(value)) return "ice-cream";
  if (/(retail|shop|fashion|clothing|electronics)/.test(value)) return "retail-store";
  return "other";
}

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function normalizeBusinessType(value: string): BusinessType {
  if (value === "retail-store") return "retail";
  if (value === "ice-cream") return "ice_cream";
  const allowed: BusinessType[] = ["restaurant", "cafe", "retail", "bakery", "pizza", "burger", "salon", "grocery", "ice_cream", "other"];
  return allowed.includes(value as BusinessType) ? value as BusinessType : "other";
}

function legacyLayoutId(value?: string | null): KioskLayoutId {
  if (value === "side-navigation") return "left_category";
  if (value === "category-first") return "category_gate";
  return "top_category";
}

function validOrderModes(values?: string[]): OrderType[] {
  const allowed: OrderType[] = ["dine_in", "takeaway", "delivery", "pickup"];
  const selected = (values || []).filter((value): value is OrderType => allowed.includes(value as OrderType));
  return selected.length ? selected : ["dine_in", "takeaway"];
}

function presetItemType(preset: MenuPreset, businessType: BusinessType): ItemType {
  if (preset.foodType) return preset.foodType === "non-veg" ? "non_veg" : "veg";
  if (businessType === "salon" || preset.category === "Services") return "service";
  if (businessType === "retail" || businessType === "grocery" || preset.category === "Products") return "retail";
  return "other";
}

function presetDescription(preset: MenuPreset, businessType: BusinessType) {
  if (businessType === "salon") return `${preset.category} service`;
  if (businessType === "retail" || businessType === "grocery") return `Available from ${preset.category}`;
  return `Freshly prepared ${preset.category.toLowerCase()} item`;
}
