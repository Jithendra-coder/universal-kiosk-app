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

const foodTags = ["Popular", "New", "Trending", "Bestseller", "Recommended", "Combo", "Deal", "Discount", "Vegan", "Spicy"];
const foodFilters: CapabilityFilter[] = ["priceSort", "veg", "nonVeg", "egg", "vegan", "spicy", "popular", "new", "deals", "combos", "discounted", "available"];
const foodActions: StartScreenAction[] = [
  { id: "dine_in", title: "Dine In", subtitle: "Order for a table", orderType: "dine_in" },
  { id: "takeaway", title: "Take Away", subtitle: "Collect at the counter", orderType: "takeaway" },
  { id: "start_order", title: "Start Order", subtitle: "Browse the full menu" },
  { id: "view_offers", title: "View Offers", subtitle: "See current deals" },
];

const bakeryActions: StartScreenAction[] = [
  { id: "order_now", title: "Order Now", subtitle: "Choose fresh items", orderType: "takeaway" },
  { id: "preorder_cake", title: "Pre-order Cake", subtitle: "Reserve cake pickup", orderType: "pickup" },
  { id: "takeaway", title: "Take Away", subtitle: "Collect at the counter", orderType: "takeaway" },
  { id: "fresh_items", title: "View Fresh Items", subtitle: "See today baked picks" },
];

const capabilities: Record<BusinessType, BusinessCapability> = {
  restaurant: {
    type: "restaurant",
    productNoun: "menu item",
    productNounPlural: "menu items",
    cartNoun: "cart",
    checkoutTitle: "Your Cart",
    checkoutCta: "Place Order",
    checkoutBlockedLabel: "Enter name to continue",
    emptyCartTitle: "Cart is empty",
    addItemsLabel: "Add items",
    confirmationTitle: "Order placed",
    confirmationMessage: "Please head to the counter. Your order is being prepared.",
    customerNameLabel: "Customer name",
    customerNameHelper: "Staff will call this name when your order is ready.",
    customerNamePlaceholder: "Enter your first name",
    tableLabel: "Table / Token",
    notesLabel: "Order notes",
    allowedOrderModes: ["dine_in", "takeaway"],
    itemTypes: ["veg", "non_veg", "other"],
    supportedFilters: foodFilters,
    supportedTags: foodTags,
    variantTypes: ["Small", "Medium", "Large", "Regular", "Family"],
    startScreenActions: foodActions,
    serviceBookingEnabled: false,
    kitchenEnabled: true,
    inventoryEnabled: true,
    appointmentEnabled: false,
    paymentEnabled: true,
    showFoodTypeBadges: true,
    orderModeLabel: "Order type",
  },
  pizza: {
    type: "pizza",
    productNoun: "menu item",
    productNounPlural: "menu items",
    cartNoun: "cart",
    checkoutTitle: "Your Cart",
    checkoutCta: "Place Order",
    checkoutBlockedLabel: "Enter name to continue",
    emptyCartTitle: "Cart is empty",
    addItemsLabel: "Add items",
    confirmationTitle: "Order placed",
    confirmationMessage: "Please head to the counter. Your order is being prepared.",
    customerNameLabel: "Customer name",
    customerNameHelper: "Staff will call this name when your order is ready.",
    customerNamePlaceholder: "Enter your first name",
    tableLabel: "Table / Token",
    notesLabel: "Order notes",
    allowedOrderModes: ["dine_in", "takeaway"],
    itemTypes: ["veg", "non_veg", "other"],
    supportedFilters: foodFilters,
    supportedTags: foodTags,
    variantTypes: ["Small", "Medium", "Large", "Regular", "Family"],
    startScreenActions: foodActions,
    serviceBookingEnabled: false,
    kitchenEnabled: true,
    inventoryEnabled: true,
    appointmentEnabled: false,
    paymentEnabled: true,
    showFoodTypeBadges: true,
    orderModeLabel: "Order type",
  },
  bakery: {
    type: "bakery",
    productNoun: "bakery item",
    productNounPlural: "bakery items",
    cartNoun: "cart",
    checkoutTitle: "Your Cart",
    checkoutCta: "Place Order",
    checkoutBlockedLabel: "Enter name to continue",
    emptyCartTitle: "Cart is empty",
    addItemsLabel: "Add items",
    confirmationTitle: "Order confirmed",
    confirmationMessage: "Your bakery order is confirmed. Please check the pickup time and payment status.",
    customerNameLabel: "Customer name",
    customerNameHelper: "Staff will call this name when your order is ready.",
    customerNamePlaceholder: "Enter your first name",
    tableLabel: "Pickup date / time",
    notesLabel: "Special instructions",
    allowedOrderModes: ["takeaway", "pickup"],
    itemTypes: ["veg", "other"],
    supportedFilters: ["priceSort", "veg", "popular", "new", "deals", "discounted", "available"],
    supportedTags: ["Popular", "New", "Bestseller", "Recommended", "Deal", "Discount"],
    variantTypes: ["Single", "Pack", "Box", "Family"],
    startScreenActions: bakeryActions,
    serviceBookingEnabled: false,
    kitchenEnabled: true,
    inventoryEnabled: true,
    appointmentEnabled: false,
    paymentEnabled: true,
    showFoodTypeBadges: true,
    orderModeLabel: "Order type",
  },
  cafe: {
    type: "cafe",
    productNoun: "drink or item",
    productNounPlural: "drinks and items",
    cartNoun: "cart",
    checkoutTitle: "Your Cart",
    checkoutCta: "Place Order",
    checkoutBlockedLabel: "Enter name to continue",
    emptyCartTitle: "Cart is empty",
    addItemsLabel: "Add drinks",
    confirmationTitle: "Order placed",
    confirmationMessage: "Please head to the counter. Your drink is being prepared.",
    customerNameLabel: "Customer name",
    customerNameHelper: "Staff will call this name when your drink is ready.",
    customerNamePlaceholder: "Enter your first name",
    tableLabel: "Table / Token",
    notesLabel: "Drink notes",
    allowedOrderModes: ["dine_in", "takeaway"],
    itemTypes: ["other", "veg", "non_veg"],
    supportedFilters: ["priceSort", "hot", "iced", "milkBased", "nonCoffee", "popular", "new", "deals", "discounted", "available"],
    supportedTags: ["Popular", "New", "Bestseller", "Recommended", "Hot", "Iced", "Milk Based", "Non Coffee", "Happy Hour", "Deal", "Discount"],
    variantTypes: ["Small", "Medium", "Large", "Hot", "Iced", "Sugar level", "Milk type", "Caffeine"],
    startScreenActions: foodActions,
    serviceBookingEnabled: false,
    kitchenEnabled: true,
    inventoryEnabled: true,
    appointmentEnabled: false,
    paymentEnabled: true,
    showFoodTypeBadges: false,
    orderModeLabel: "Order type",
  },
  burger: {
    type: "burger",
    productNoun: "burger item",
    productNounPlural: "burger items",
    cartNoun: "cart",
    checkoutTitle: "Your Cart",
    checkoutCta: "Place Order",
    checkoutBlockedLabel: "Enter name to continue",
    emptyCartTitle: "Cart is empty",
    addItemsLabel: "Add items",
    confirmationTitle: "Order placed",
    confirmationMessage: "Your burger order is placed. Please watch for the preparation status.",
    customerNameLabel: "Customer name",
    customerNameHelper: "Staff will call this name when your order is ready.",
    customerNamePlaceholder: "Enter your first name",
    tableLabel: "Table / pickup name",
    notesLabel: "Special instructions",
    allowedOrderModes: ["dine_in", "takeaway"],
    itemTypes: ["veg", "non_veg", "other"],
    supportedFilters: foodFilters,
    supportedTags: foodTags,
    variantTypes: ["Patty type", "Cheese option", "Sauce", "Combo", "Add-on"],
    startScreenActions: foodActions,
    serviceBookingEnabled: false,
    kitchenEnabled: true,
    inventoryEnabled: true,
    appointmentEnabled: false,
    paymentEnabled: true,
    showFoodTypeBadges: true,
    orderModeLabel: "Order type",
  },
  salon: {
    type: "salon",
    productNoun: "service",
    productNounPlural: "services",
    cartNoun: "booking",
    checkoutTitle: "Confirm Booking",
    checkoutCta: "Confirm Booking",
    checkoutBlockedLabel: "Enter name to continue",
    emptyCartTitle: "No services selected",
    addItemsLabel: "Add services",
    confirmationTitle: "Booking confirmed",
    confirmationMessage: "Your appointment is confirmed. Please check service, staff, date, time, and payment status.",
    customerNameLabel: "Customer name",
    customerNameHelper: "Staff will call this name when your stylist is ready.",
    customerNamePlaceholder: "Enter customer name",
    tableLabel: "Stylist / Slot",
    notesLabel: "Service notes",
    allowedOrderModes: ["pickup"],
    itemTypes: ["service", "retail", "other"],
    supportedFilters: ["priceSort", "popular", "new", "deals", "discounted", "available"],
    supportedTags: ["Popular", "New", "Recommended", "Package", "Deal", "Discount", "Walk-in"],
    variantTypes: ["Duration", "Stylist", "Slot", "Package", "Add-on"],
    startScreenActions: [
      { id: "book_appointment", title: "Book Appointment", subtitle: "Choose service and time", orderType: "pickup" },
      { id: "view_services", title: "View Services", subtitle: "Browse all services", orderType: "pickup" },
      { id: "choose_staff", title: "Choose Staff", subtitle: "Pick preferred stylist", orderType: "pickup" },
      { id: "my_booking", title: "My Booking", subtitle: "Review booking details", orderType: "pickup" },
    ],
    serviceBookingEnabled: true,
    kitchenEnabled: false,
    inventoryEnabled: true,
    appointmentEnabled: true,
    paymentEnabled: true,
    showFoodTypeBadges: false,
    orderModeLabel: "Service mode",
  },
  retail: {
    type: "retail",
    productNoun: "product",
    productNounPlural: "products",
    cartNoun: "cart",
    checkoutTitle: "Shopping Cart",
    checkoutCta: "Confirm Purchase",
    checkoutBlockedLabel: "Enter phone to continue",
    emptyCartTitle: "Cart is empty",
    addItemsLabel: "Add products",
    confirmationTitle: "Purchase confirmed",
    confirmationMessage: "Your purchase is confirmed. Please check pickup or delivery status and payment status.",
    customerNameLabel: "Customer phone number",
    customerNameHelper: "Staff will use this phone number for pickup, delivery, and billing.",
    customerNamePlaceholder: "Enter phone number",
    tableLabel: "Pickup / delivery note",
    notesLabel: "Order notes",
    allowedOrderModes: ["pickup", "delivery"],
    itemTypes: ["retail", "other"],
    supportedFilters: ["priceSort", "popular", "new", "deals", "discounted", "available"],
    supportedTags: ["Popular", "New", "Featured", "Recommended", "Deal", "Discount"],
    variantTypes: ["Variant", "Size", "Pack", "Color", "Brand"],
    startScreenActions: [
      { id: "start_shopping", title: "Start Shopping", subtitle: "Browse products", orderType: "pickup" },
      { id: "browse_categories", title: "Browse Categories", subtitle: "Explore departments", orderType: "pickup" },
      { id: "scan_product", title: "Scan Product", subtitle: "Find by barcode", orderType: "pickup" },
      { id: "view_offers", title: "View Offers", subtitle: "See current deals", orderType: "pickup" },
    ],
    serviceBookingEnabled: false,
    kitchenEnabled: false,
    inventoryEnabled: true,
    appointmentEnabled: false,
    paymentEnabled: true,
    showFoodTypeBadges: false,
    orderModeLabel: "Pickup or delivery",
  },
  grocery: {
    type: "grocery",
    productNoun: "product",
    productNounPlural: "products",
    cartNoun: "cart",
    checkoutTitle: "Shopping Cart",
    checkoutCta: "Place Order",
    checkoutBlockedLabel: "Enter phone to continue",
    emptyCartTitle: "Cart is empty",
    addItemsLabel: "Add products",
    confirmationTitle: "Shopping order placed",
    confirmationMessage: "Your shopping order is placed. Please check pickup or delivery status and payment status.",
    customerNameLabel: "Customer phone number",
    customerNameHelper: "Staff will use this phone number for pickup, delivery, and billing.",
    customerNamePlaceholder: "Enter phone number",
    tableLabel: "Bag / pickup note",
    notesLabel: "Order notes",
    allowedOrderModes: ["pickup", "delivery"],
    itemTypes: ["retail", "other"],
    supportedFilters: ["priceSort", "popular", "new", "deals", "discounted", "available"],
    supportedTags: ["Popular", "New", "Featured", "Recommended", "Deal", "Discount"],
    variantTypes: ["Weight", "Pack size", "Brand", "Variant"],
    startScreenActions: [
      { id: "start_shopping", title: "Start Shopping", subtitle: "Browse grocery items", orderType: "pickup" },
      { id: "scan_product", title: "Scan Product", subtitle: "Find by barcode", orderType: "pickup" },
      { id: "view_offers", title: "View Offers", subtitle: "See current deals", orderType: "pickup" },
      { id: "call_staff", title: "Call Staff", subtitle: "Ask for help" },
    ],
    serviceBookingEnabled: false,
    kitchenEnabled: false,
    inventoryEnabled: true,
    appointmentEnabled: false,
    paymentEnabled: true,
    showFoodTypeBadges: false,
    orderModeLabel: "Pickup or delivery",
  },
  ice_cream: {
    type: "ice_cream",
    productNoun: "ice cream item",
    productNounPlural: "ice cream items",
    cartNoun: "cart",
    checkoutTitle: "Your Cart",
    checkoutCta: "Place Order",
    checkoutBlockedLabel: "Enter name to continue",
    emptyCartTitle: "Cart is empty",
    addItemsLabel: "Add ice cream",
    confirmationTitle: "Order placed",
    confirmationMessage: "Your ice cream order is placed. Please watch for the preparation status.",
    customerNameLabel: "Customer name",
    customerNameHelper: "Staff will call this name when your order is ready.",
    customerNamePlaceholder: "Enter your first name",
    tableLabel: "Table / pickup name",
    notesLabel: "Special instructions",
    allowedOrderModes: ["dine_in", "takeaway"],
    itemTypes: ["veg", "other"],
    supportedFilters: ["priceSort", "veg", "popular", "new", "bestseller", "recommended", "deals", "combos", "discounted", "available"],
    supportedTags: ["Popular", "New", "Bestseller", "Recommended", "Combo", "Deal", "Discount"],
    variantTypes: ["Cup", "Cone", "Single scoop", "Double scoop", "Toppings", "Syrup"],
    startScreenActions: [
      { id: "dine_in", title: "Dine In", subtitle: "Enjoy in store", orderType: "dine_in" },
      { id: "takeaway", title: "Take Away", subtitle: "Collect at the counter", orderType: "takeaway" },
      { id: "start_order", title: "Start Order", subtitle: "Browse flavors and treats" },
      { id: "view_offers", title: "View Offers", subtitle: "See current deals" },
    ],
    serviceBookingEnabled: false,
    kitchenEnabled: true,
    inventoryEnabled: true,
    appointmentEnabled: false,
    paymentEnabled: true,
    showFoodTypeBadges: true,
    orderModeLabel: "Order type",
  },
  other: {
    type: "other",
    productNoun: "item",
    productNounPlural: "items",
    cartNoun: "cart",
    checkoutTitle: "Review Selection",
    checkoutCta: "Submit",
    checkoutBlockedLabel: "Enter name to continue",
    emptyCartTitle: "Nothing selected",
    addItemsLabel: "Add items",
    confirmationTitle: "Request received",
    confirmationMessage: "Please head to the counter. Your request is being prepared.",
    customerNameLabel: "Customer name",
    customerNameHelper: "Staff will use this name to call you.",
    customerNamePlaceholder: "Enter customer name",
    tableLabel: "Reference",
    notesLabel: "Notes",
    allowedOrderModes: ["pickup"],
    itemTypes: ["service", "retail", "other"],
    supportedFilters: ["priceSort", "popular", "new", "deals", "discounted", "available"],
    supportedTags: ["Popular", "New", "Featured", "Recommended", "Deal", "Discount"],
    variantTypes: ["Option", "Package", "Add-on"],
    startScreenActions: [
      { id: "browse", title: "Browse Items", subtitle: "View available items", orderType: "pickup" },
      { id: "services", title: "View Services", subtitle: "Browse service options", orderType: "pickup" },
    ],
    serviceBookingEnabled: true,
    kitchenEnabled: false,
    inventoryEnabled: true,
    appointmentEnabled: false,
    paymentEnabled: true,
    showFoodTypeBadges: false,
    orderModeLabel: "Selection type",
  },
};

export function businessCapabilities(type?: BusinessType | null): BusinessCapability {
  return capabilities[type ?? "restaurant"] ?? capabilities.restaurant;
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
