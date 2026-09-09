from typing import Any, Dict, List, Optional
from schemas import BusinessType

KIOSK_LAYOUT_IDS = ["top_category", "left_category", "category_gate"]
KIOSK_CARD_STYLES = ["auto", "compact", "detailed", "image_focused", "fast_add"]
KIOSK_CATEGORY_STYLES = ["simple_button", "picture_card", "image_cards", "motion_tabs"]
KIOSK_PRODUCT_DISPLAY_STYLES = ["simple_item", "detailed_card", "grid", "dense_fast_add_list"]
KIOSK_ACTION_BEHAVIORS = ["auto", "direct_add", "customize_first", "variant_select", "quantity_stepper", "booking"]
DEFAULT_KIOSK_ACCENT = "#000000"

FOOD_BASE = {
    "allowedLayouts": KIOSK_LAYOUT_IDS,
    "flowType": "cart",
    "itemNoun": "item",
    "itemNounPlural": "items",
    "startLabel": "Start Your Order",
    "secondaryStartLabel": "View Menu",
    "checkoutLabel": "Checkout",
    "emptyLabel": "No items found",
    "showStock": False,
    "showUnit": False,
    "showBrand": False,
    "showDuration": False,
    "showVariants": True,
    "showAddons": True,
    "defaultCategoryStyle": "simple_button",
    "defaultProductDisplayStyle": "detailed_card",
}

CONFIGS: Dict[str, Dict[str, Any]] = {
    "restaurant": {
        **FOOD_BASE,
        "type": "restaurant",
        "defaultLayout": "top_category",
        "showPrepTime": True,
        "showDietaryType": True,
        "showCombos": True,
        "defaultCardStyle": "detailed",
        "defaultActionBehavior": "direct_add",
    },
    "cafe": {
        **FOOD_BASE,
        "type": "cafe",
        "defaultLayout": "top_category",
        "showPrepTime": True,
        "showDietaryType": True,
        "showCombos": True,
        "defaultCardStyle": "compact",
        "defaultActionBehavior": "direct_add",
    },
    "pizza": {
        **FOOD_BASE,
        "type": "pizza",
        "defaultLayout": "top_category",
        "showPrepTime": True,
        "showDietaryType": True,
        "showCombos": True,
        "defaultCardStyle": "detailed",
        "defaultActionBehavior": "customize_first",
    },
    "burger": {
        **FOOD_BASE,
        "type": "burger",
        "defaultLayout": "top_category",
        "showPrepTime": True,
        "showDietaryType": True,
        "showCombos": True,
        "defaultCardStyle": "detailed",
        "defaultActionBehavior": "customize_first",
    },
    "bakery": {
        **FOOD_BASE,
        "type": "bakery",
        "defaultLayout": "category_gate",
        "showPrepTime": False,
        "showDietaryType": True,
        "showStock": True,
        "showUnit": True,
        "showCombos": True,
        "defaultCardStyle": "image_focused",
        "defaultActionBehavior": "direct_add",
    },
    "ice_cream": {
        **FOOD_BASE,
        "type": "ice_cream",
        "defaultLayout": "top_category",
        "showPrepTime": False,
        "showDietaryType": True,
        "showCombos": True,
        "defaultCardStyle": "image_focused",
        "defaultActionBehavior": "customize_first",
    },
    "grocery": {
        "type": "grocery",
        "allowedLayouts": KIOSK_LAYOUT_IDS,
        "defaultLayout": "category_gate",
        "flowType": "cart",
        "itemNoun": "product",
        "itemNounPlural": "products",
        "startLabel": "Start Shopping",
        "secondaryStartLabel": "Browse Products",
        "checkoutLabel": "Checkout",
        "emptyLabel": "No products found",
        "showPrepTime": False,
        "showDietaryType": False,
        "showStock": True,
        "showUnit": True,
        "showBrand": True,
        "showDuration": False,
        "showVariants": True,
        "showAddons": False,
        "showCombos": False,
        "defaultCardStyle": "compact",
        "defaultCategoryStyle": "simple_button",
        "defaultProductDisplayStyle": "detailed_card",
        "defaultActionBehavior": "quantity_stepper",
    },
    "retail": {
        "type": "retail",
        "allowedLayouts": KIOSK_LAYOUT_IDS,
        "defaultLayout": "category_gate",
        "flowType": "cart",
        "itemNoun": "product",
        "itemNounPlural": "products",
        "startLabel": "Start Shopping",
        "secondaryStartLabel": "Browse Products",
        "checkoutLabel": "Checkout",
        "emptyLabel": "No products found",
        "showPrepTime": False,
        "showDietaryType": False,
        "showStock": True,
        "showUnit": False,
        "showBrand": True,
        "showDuration": False,
        "showVariants": True,
        "showAddons": False,
        "showCombos": False,
        "defaultCardStyle": "compact",
        "defaultCategoryStyle": "simple_button",
        "defaultProductDisplayStyle": "detailed_card",
        "defaultActionBehavior": "quantity_stepper",
    },
    "salon": {
        "type": "salon",
        "allowedLayouts": KIOSK_LAYOUT_IDS,
        "defaultLayout": "category_gate",
        "flowType": "booking",
        "itemNoun": "service",
        "itemNounPlural": "services",
        "startLabel": "Book a Service",
        "secondaryStartLabel": "Browse Services",
        "checkoutLabel": "Confirm Booking",
        "emptyLabel": "No services found",
        "showPrepTime": False,
        "showDietaryType": False,
        "showStock": False,
        "showUnit": False,
        "showBrand": False,
        "showDuration": True,
        "showVariants": True,
        "showAddons": True,
        "showCombos": True,
        "defaultCardStyle": "detailed",
        "defaultCategoryStyle": "simple_button",
        "defaultProductDisplayStyle": "detailed_card",
        "defaultActionBehavior": "booking",
    },
    "other": {
        "type": "other",
        "allowedLayouts": KIOSK_LAYOUT_IDS,
        "defaultLayout": "top_category",
        "flowType": "cart",
        "itemNoun": "item",
        "itemNounPlural": "items",
        "startLabel": "Get Started",
        "secondaryStartLabel": "Browse Items",
        "checkoutLabel": "Continue",
        "emptyLabel": "No items found",
        "showPrepTime": False,
        "showDietaryType": False,
        "showStock": False,
        "showUnit": False,
        "showBrand": False,
        "showDuration": False,
        "showVariants": True,
        "showAddons": True,
        "showCombos": False,
        "defaultCardStyle": "compact",
        "defaultCategoryStyle": "simple_button",
        "defaultProductDisplayStyle": "detailed_card",
        "defaultActionBehavior": "direct_add",
    },
}


def get_kiosk_business_config(business_type: Optional[str | BusinessType] = None) -> Dict[str, Any]:
    raw_type = business_type.value if isinstance(business_type, BusinessType) else (business_type or "restaurant")
    return CONFIGS.get(raw_type, CONFIGS["restaurant"])


def resolve_kiosk_display_settings(business_type: Optional[str | BusinessType], settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config = get_kiosk_business_config(business_type)
    settings = settings or {}

    selected_layout = settings.get("selectedLayout") or config["defaultLayout"]
    if selected_layout not in config["allowedLayouts"]:
        selected_layout = config["defaultLayout"]

    card_style = settings.get("cardStyle") or "auto"
    if card_style == "auto":
        card_style = config["defaultCardStyle"]

    category_style = settings.get("categoryStyle") or config["defaultCategoryStyle"]
    product_display_style = settings.get("productDisplayStyle") or config["defaultProductDisplayStyle"]

    action_behavior = settings.get("actionBehavior") or "auto"
    if action_behavior == "auto":
        action_behavior = config["defaultActionBehavior"]

    accent_color = settings.get("accentColor") or DEFAULT_KIOSK_ACCENT

    return {
        "selectedLayout": selected_layout,
        "cardStyle": card_style,
        "categoryStyle": category_style,
        "productDisplayStyle": product_display_style,
        "actionBehavior": action_behavior,
        "accentColor": accent_color,
    }
