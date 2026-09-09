import type { Business, BusinessType, ItemType, OrderType } from "@/lib/types";

export type CapabilityFilter =
  | "veg"
  | "nonVeg"
  | "egg"
  | "vegan"
  | "spicy"
  | "popular"
  | "new"
  | "bestseller"
  | "recommended"
  | "hot"
  | "iced"
  | "milkBased"
  | "nonCoffee"
  | "deals"
  | "combos"
  | "discounted"
  | "available"
  | "priceSort";

export type StartScreenAction = {
  id: string;
  title: string;
  subtitle: string;
  orderType?: OrderType;
};

export type BusinessCapability = {
  type: BusinessType;
  productNoun: string;
  productNounPlural: string;
  cartNoun: string;
  checkoutTitle: string;
  checkoutCta: string;
  checkoutBlockedLabel: string;
  emptyCartTitle: string;
  addItemsLabel: string;
  confirmationTitle: string;
  confirmationMessage: string;
  customerNameLabel: string;
  customerNameHelper: string;
  customerNamePlaceholder: string;
  tableLabel: string;
  notesLabel: string;
  allowedOrderModes: OrderType[];
  itemTypes: ItemType[];
  supportedFilters: CapabilityFilter[];
  supportedTags: string[];
  variantTypes: string[];
  startScreenActions: StartScreenAction[];
  serviceBookingEnabled: boolean;
  kitchenEnabled: boolean;
  inventoryEnabled: boolean;
  appointmentEnabled: boolean;
  paymentEnabled: boolean;
  showFoodTypeBadges: boolean;
  orderModeLabel: string;
};

const BASE_CAPABILITY: Omit<BusinessCapability, "type"> = {
  productNoun: "item",
  productNounPlural: "items",
  cartNoun: "order",
  checkoutTitle: "Review Your Order",
  checkoutCta: "Place Order",
  checkoutBlockedLabel: "Select dining option to continue",
  emptyCartTitle: "Your tray is empty",
  addItemsLabel: "Add items to start",
  confirmationTitle: "Order placed",
  confirmationMessage: "We've received your order. Please take your token receipt.",
  customerNameLabel: "Name for callout",
  customerNameHelper: "We'll announce this name when your food is ready.",
  customerNamePlaceholder: "e.g. Alex",
  tableLabel: "Table number",
  notesLabel: "Kitchen instructions",
  allowedOrderModes: ["dine_in", "takeaway"],
  itemTypes: ["veg", "non_veg"],
  supportedFilters: ["veg", "nonVeg", "spicy", "popular", "bestseller", "recommended", "combos", "discounted", "available", "priceSort"],
  supportedTags: ["Chef Special", "Spicy", "Bestseller", "New", "Must Try", "Popular"],
  variantTypes: ["Portion", "Spice Level", "Preparation"],
  startScreenActions: [
    { id: "dine_in", title: "Dine In", subtitle: "Enjoy your meal here", orderType: "dine_in" },
    { id: "takeaway", title: "Takeaway", subtitle: "Pack for pickup", orderType: "takeaway" },
  ],
  serviceBookingEnabled: false,
  kitchenEnabled: true,
  inventoryEnabled: true,
  appointmentEnabled: false,
  paymentEnabled: true,
  showFoodTypeBadges: true,
  orderModeLabel: "Dining preference",
};

const TYPE_OVERRIDES: Partial<Record<BusinessType, Partial<BusinessCapability>>> = {
  restaurant: { productNoun: "dish", productNounPlural: "dishes", addItemsLabel: "Add dishes to start", confirmationTitle: "Order sent to kitchen" },
  cafe: {
    cartNoun: "tray", checkoutTitle: "Your Cafe Order", checkoutCta: "Brew It", checkoutBlockedLabel: "Select pickup mode to continue",
    addItemsLabel: "Pick a beverage or treat", customerNameLabel: "Cup name", customerNameHelper: "Printed on your cup label.",
    customerNamePlaceholder: "Name for the cup", tableLabel: "Table / Seat", notesLabel: "Barista notes", itemTypes: ["veg", "non_veg", "other"],
    supportedFilters: ["hot", "iced", "milkBased", "nonCoffee", "veg", "popular", "new", "deals", "discounted", "available", "priceSort"],
    supportedTags: ["Hot", "Iced", "Signature Roast", "Seasonal", "Popular", "Dairy Free"], variantTypes: ["Cup Size", "Bean Blend", "Milk Choice", "Sweetness"],
    startScreenActions: [{ id: "order_now", title: "Order Now", subtitle: "Coffee, drinks & bites", orderType: "dine_in" }, { id: "takeaway", title: "To Go", subtitle: "Quick grab & run", orderType: "takeaway" }],
    orderModeLabel: "Order type",
  },
  retail: {
    productNoun: "product", productNounPlural: "products", cartNoun: "bag", checkoutTitle: "Self-Checkout", checkoutCta: "Pay Now",
    checkoutBlockedLabel: "Scan or select items to continue", emptyCartTitle: "Your shopping bag is empty", addItemsLabel: "Scan barcodes or tap products",
    confirmationTitle: "Payment complete", confirmationMessage: "Please collect your printed receipt and bag your items.", customerNameLabel: "Customer name",
    customerNameHelper: "Optional for receipt and warranty lookup.", customerNamePlaceholder: "Optional name or phone", tableLabel: "Bag / Locker #",
    notesLabel: "Packing notes", allowedOrderModes: ["pickup"], itemTypes: ["retail"], supportedFilters: ["popular", "new", "bestseller", "deals", "discounted", "available", "priceSort"],
    supportedTags: ["Trending", "Limited Stock", "New Arrival", "Bestseller", "Sale"], variantTypes: ["Size", "Color", "Material", "Pack"],
    startScreenActions: [{ id: "self_checkout", title: "Self-Checkout", subtitle: "Scan or select & pay", orderType: "pickup" }],
    kitchenEnabled: false, showFoodTypeBadges: false, orderModeLabel: "Checkout",
  },
  bakery: {
    productNoun: "bake", productNounPlural: "bakes", cartNoun: "box", checkoutTitle: "Bakery Box", checkoutCta: "Box It Up",
    checkoutBlockedLabel: "Select pack preference", emptyCartTitle: "Box is empty", addItemsLabel: "Add fresh bakes", confirmationTitle: "Bakes reserved",
    confirmationMessage: "Your box is being packed at the bakery counter.", customerNameLabel: "Box label name", customerNameHelper: "We'll label your box with this name.",
    customerNamePlaceholder: "Customer name", tableLabel: "Counter spot", notesLabel: "Packaging instructions",
    supportedFilters: ["veg", "egg", "vegan", "popular", "new", "bestseller", "deals", "discounted", "available", "priceSort"],
    supportedTags: ["Warm", "Eggless", "Fresh Out", "Artisanal", "Bestseller"], variantTypes: ["Weight", "Piece Count", "Box Size"],
    startScreenActions: [{ id: "box_to_go", title: "Box to Go", subtitle: "Pack for takeaway", orderType: "takeaway" }, { id: "enjoy_here", title: "Enjoy Here", subtitle: "Bakery cafe seating", orderType: "dine_in" }],
    orderModeLabel: "Packaging type",
  },
  pizza: {
    productNoun: "pizza", productNounPlural: "pizzas", checkoutTitle: "Review Pizza Order", checkoutCta: "Fire Up the Oven", checkoutBlockedLabel: "Select crust & size",
    emptyCartTitle: "No pizzas yet", addItemsLabel: "Pick a signature pie", confirmationTitle: "Pizzas in the oven!", confirmationMessage: "We'll call your number when your crust is golden brown.",
    customerNameLabel: "Order name", customerNameHelper: "For order pickup callout.", customerNamePlaceholder: "Name for callout", notesLabel: "Baking instructions",
    supportedFilters: ["veg", "nonVeg", "spicy", "combos", "deals", "popular", "bestseller", "discounted", "available", "priceSort"],
    supportedTags: ["Wood Fired", "Spicy", "Chef Special", "Loaded Cheese", "Bestseller"], variantTypes: ["Crust", "Size", "Cheese Blend"],
    startScreenActions: [{ id: "dine_in", title: "Dine In", subtitle: "Hot slice at your table", orderType: "dine_in" }, { id: "takeaway", title: "Takeaway Box", subtitle: "Hot to take home", orderType: "takeaway" }],
    orderModeLabel: "Dining mode",
  },
  burger: {
    productNoun: "burger", productNounPlural: "burgers", cartNoun: "combo tray", checkoutTitle: "Complete Your Stack", checkoutCta: "Grill It",
    checkoutBlockedLabel: "Select meal options", emptyCartTitle: "Tray is clear", addItemsLabel: "Pick a burger or meal", confirmationTitle: "Order sizzling!",
    confirmationMessage: "Grilling your patties now. Keep your receipt handy.", customerNameLabel: "Pickup name", customerNameHelper: "Announced on the pickup speakers.",
    customerNamePlaceholder: "Customer name", tableLabel: "Table tent #", notesLabel: "Grill instructions",
    supportedFilters: ["veg", "nonVeg", "spicy", "combos", "deals", "popular", "bestseller", "discounted", "available", "priceSort"],
    supportedTags: ["Double Patty", "Smash", "Crispy", "Spicy", "Bestseller", "Meal Deal"], variantTypes: ["Patty Count", "Bun Type", "Meal Upgrade"],
    startScreenActions: [{ id: "eat_here", title: "Eat Here", subtitle: "Tray service", orderType: "dine_in" }, { id: "takeaway", title: "Take Out", subtitle: "Bagged & ready", orderType: "takeaway" }],
    orderModeLabel: "Tray type",
  },
  salon: {
    productNoun: "service", productNounPlural: "services", cartNoun: "booking", checkoutTitle: "Confirm Your Appointment", checkoutCta: "Book Appointment",
    checkoutBlockedLabel: "Select customer name & stylist", emptyCartTitle: "No services selected", addItemsLabel: "Choose salon services",
    confirmationTitle: "Booking confirmed", confirmationMessage: "Your stylist will be ready for you shortly. Please take a seat.", customerNameLabel: "Client name",
    customerNameHelper: "Stylist will call you by this name.", customerNamePlaceholder: "Your name", tableLabel: "Station / Chair", notesLabel: "Styling preferences",
    allowedOrderModes: ["dine_in"], itemTypes: ["service", "retail"], supportedFilters: ["popular", "recommended", "new", "deals", "discounted", "available", "priceSort"],
    supportedTags: ["Express", "Signature", "Organic", "Popular", "Consultation"], variantTypes: ["Hair Length", "Stylist Level", "Add-on Treatment"],
    startScreenActions: [{ id: "walk_in", title: "Walk-in Service", subtitle: "Check in & select services", orderType: "dine_in" }, { id: "retail", title: "Hair & Body Care", subtitle: "Browse salon products", orderType: "dine_in" }],
    serviceBookingEnabled: true, kitchenEnabled: false, appointmentEnabled: true, showFoodTypeBadges: false, orderModeLabel: "Service mode",
  },
  grocery: {
    productNoun: "item", productNounPlural: "items", cartNoun: "basket", checkoutTitle: "Express Checkout", checkoutCta: "Pay & Bag",
    checkoutBlockedLabel: "Scan items to continue", emptyCartTitle: "Basket is empty", addItemsLabel: "Scan or select items",
    confirmationTitle: "Receipt ready", confirmationMessage: "Payment verified. Please take your receipt and pack your bags.",
    customerNameLabel: "Member name", customerNameHelper: "For loyalty points and rewards.", customerNamePlaceholder: "Name or Member ID",
    tableLabel: "Lane number", notesLabel: "Bagging preference", allowedOrderModes: ["pickup"], itemTypes: ["retail"],
    supportedFilters: ["deals", "discounted", "popular", "available", "priceSort"], supportedTags: ["Organic", "Farm Fresh", "Bulk Pack", "Offer", "Local"],
    variantTypes: ["Weight", "Pack Size", "Flavor"], startScreenActions: [{ id: "self_scan", title: "Scan & Go", subtitle: "Quick basket checkout", orderType: "pickup" }],
    kitchenEnabled: false, showFoodTypeBadges: false, orderModeLabel: "Checkout lane",
  },
  ice_cream: {
    productNoun: "scoop", productNounPlural: "scoops", cartNoun: "cup / cone", checkoutTitle: "Your Sweet Treat", checkoutCta: "Scoop It!",
    checkoutBlockedLabel: "Pick your container", emptyCartTitle: "Cup is empty", addItemsLabel: "Choose your flavors",
    confirmationTitle: "Scooping now!", confirmationMessage: "Head to the pickup station to collect your treat.", customerNameLabel: "Name",
    customerNameHelper: "We'll call your name at the scoop counter.", customerNamePlaceholder: "Name for callout", tableLabel: "Seating",
    notesLabel: "Allergy notes", itemTypes: ["veg", "other"], supportedFilters: ["vegan", "veg", "popular", "new", "deals", "discounted", "available", "priceSort"],
    supportedTags: ["Dairy Free", "Seasonal", "Double Scoop", "Popular", "Kids Fav"], variantTypes: ["Container (Cup/Waffle)", "Scoop Count", "Topping"],
    startScreenActions: [{ id: "scoop_now", title: "Scoop Here", subtitle: "Enjoy in the parlor", orderType: "dine_in" }, { id: "takeaway", title: "Pack to Go", subtitle: "Insulated tubs & pints", orderType: "takeaway" }],
    orderModeLabel: "Container preference",
  },
  other: {
    productNoun: "item", productNounPlural: "items", cartNoun: "cart", checkoutTitle: "Review Selection", checkoutCta: "Submit",
    checkoutBlockedLabel: "Enter name to continue", emptyCartTitle: "Nothing selected", addItemsLabel: "Add items",
    confirmationTitle: "Request received", confirmationMessage: "Please head to the counter. Your request is being prepared.", customerNameLabel: "Customer name",
    customerNameHelper: "Staff will use this name to call you.", customerNamePlaceholder: "Enter customer name", tableLabel: "Reference", notesLabel: "Notes",
    allowedOrderModes: ["pickup"], itemTypes: ["service", "retail", "other"], supportedFilters: ["priceSort", "popular", "new", "deals", "discounted", "available"],
    supportedTags: ["Popular", "New", "Featured", "Recommended", "Deal", "Discount"], variantTypes: ["Option", "Package", "Add-on"],
    startScreenActions: [{ id: "browse", title: "Browse Items", subtitle: "View available items", orderType: "pickup" }, { id: "services", title: "View Services", subtitle: "Browse service options", orderType: "pickup" }],
    serviceBookingEnabled: true, kitchenEnabled: false, showFoodTypeBadges: false, orderModeLabel: "Selection type",
  },
};

const capabilityCache = new Map<string, BusinessCapability>();

export async function fetchServerCapabilities(type: BusinessType): Promise<BusinessCapability | null> {
  try {
    const res = await fetch(`/api/businesses/capabilities/${type}`);
    if (res.ok) {
      const data = await res.json();
      if (data?.capabilities) {
        capabilityCache.set(type, data.capabilities);
        return data.capabilities as BusinessCapability;
      }
    }
  } catch {}
  return null;
}

export function businessCapabilities(type?: BusinessType | null): BusinessCapability {
  const key = type ?? "restaurant";
  if (capabilityCache.has(key)) return capabilityCache.get(key)!;
  const resolved: BusinessCapability = {
    ...BASE_CAPABILITY,
    ...(TYPE_OVERRIDES[key] || {}),
    type: key,
  };
  capabilityCache.set(key, resolved);
  return resolved;
}

export function businessCapabilitiesFor(business?: Pick<Business, "type" | "order_modes"> | null): BusinessCapability {
  const base = businessCapabilities(business?.type);
  if (!business?.order_modes?.length) return base;
  const configuredModes = business.order_modes.filter((mode) => base.allowedOrderModes.includes(mode));
  return configuredModes.length ? { ...base, allowedOrderModes: configuredModes } : base;
}

export function supportedItemTypeOptions(type?: BusinessType | null) {
  const capability = businessCapabilities(type);
  const labels: Record<ItemType, string> = {
    veg: type === "pizza" ? "Veg pizza" : type === "burger" ? "Veg burger" : type === "cafe" ? "Cafe snack" : type === "ice_cream" ? "Ice cream" : "Veg",
    non_veg: type === "pizza" ? "Non-veg pizza" : type === "burger" ? "Non-veg burger" : type === "cafe" ? "Non-veg snack" : "Non-veg",
    retail: type === "salon" ? "Retail product" : "Retail item",
    service: "Service",
    other: type === "cafe" ? "Beverage / other" : type === "ice_cream" ? "Treat / other" : "Other",
  };
  return capability.itemTypes.map((id) => ({ id, label: labels[id] }));
}

export function capabilityHasFilter(capability: BusinessCapability, filter: CapabilityFilter) {
  return capability.supportedFilters.includes(filter);
}

export function capabilityHasAnyFilter(capability: BusinessCapability, filters: CapabilityFilter[]) {
  return filters.some((filter) => capabilityHasFilter(capability, filter));
}
