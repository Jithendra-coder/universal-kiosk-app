import { assetUrl } from "@/lib/api";
import { kioskBusinessConfig } from "@/lib/kiosk/kiosk-business-config";
import { discountBadge, effectivePrice } from "@/lib/product-utils";
import type { BusinessType, Product } from "@/lib/types";
import type { KioskCarouselItem, KioskDietaryType } from "@/app/_components/kiosk-product-carousel";

type Details = Record<string, unknown>;

function productDetails(product: Product): Details {
  const details = product.metadata?.business_details;
  return details && typeof details === "object" && !Array.isArray(details) ? (details as Details) : {};
}

function firstText(details: Details, keys: string[]) {
  for (const key of keys) {
    const value = details[key];
    if (typeof value === "string" && value.trim()) return value.trim();
    if (typeof value === "number") return String(value);
  }
  return undefined;
}

function modifierHint(product: Product) {
  const groups = product.modifier_groups ?? [];
  if (!groups.length) return undefined;
  return groups
    .slice(0, 2)
    .map((group) => group.name)
    .join(" · ");
}

function dietaryType(product: Product): KioskDietaryType | undefined {
  if (product.item_type === "veg") return "veg";
  if (product.item_type === "non_veg") return "non_veg";
  const details = productDetails(product);
  const raw = String(
    details.dietaryType ??
      details.dietary_type ??
      product.metadata?.dietary_type ??
      product.metadata?.food_type ??
      ""
  ).toLowerCase();
  if (raw.includes("vegan")) return "vegan";
  if (raw.includes("egg")) return "egg";
  const tags = Array.isArray(product.metadata?.tags) ? product.metadata?.tags.map(String).join(" ").toLowerCase() : "";
  if (tags.includes("vegan")) return "vegan";
  if (tags.includes("egg")) return "egg";
  return undefined;
}

function productStatus(product: Product) {
  if (!product.is_available) return { label: "Unavailable", disabled: true };
  if (product.track_stock && Number(product.stock_quantity ?? 0) <= 0) {
    return { label: "Out of stock", disabled: true };
  }
  if (product.track_stock && product.stock_quantity != null) {
    const details = productDetails(product);
    const lowStock = Number(details.low_stock_alert_quantity ?? product.metadata?.low_stock_alert_quantity ?? 0);
    if (lowStock > 0 && Number(product.stock_quantity) <= lowStock) return { label: "Low stock", disabled: false };
    return { label: `${product.stock_quantity} in stock`, disabled: false };
  }
  return { label: undefined, disabled: false };
}

export function mapProductToKioskCarouselItem(
  product: Product,
  businessType: BusinessType,
  quantityInCart: number,
  imageFallback?: string
): KioskCarouselItem {
  const config = kioskBusinessConfig(businessType);
  const details = productDetails(product);
  const status = productStatus(product);
  const unit = firstText(details, ["unit", "pack_size", "weight", "size", "portion_size", "scoop_count"]);
  const brand = firstText(details, ["brand", "manufacturer", "model"]);
  const duration = firstText(details, ["service_duration", "duration"]);
  const prepTime = firstText(details, ["prep_time", "preparation_time"]);
  const serviceType = firstText(details, ["service_type", "staff_required", "gender_type"]);
  const price = effectivePrice(product);
  const hasDiscount = price < Number(product.price || 0);

  return {
    id: product.id,
    name: product.name,
    description: product.description ?? undefined,
    imageUrl: assetUrl(product.primary_image_path) || imageFallback,
    imageFit: businessType === "grocery" || businessType === "retail" ? "contain" : "cover",
    price,
    originalPrice: hasDiscount ? Number(product.price || 0) : undefined,
    discount: discountBadge(product) ?? undefined,
    metaLabel: config.showDuration ? duration : config.showUnit ? unit : businessType === "retail" ? unit : undefined,
    secondaryMetaLabel: config.showBrand ? brand : config.flowType === "booking" ? serviceType : modifierHint(product),
    timeLabel: config.showPrepTime ? prepTime : undefined,
    statusLabel: config.showStock || status.disabled ? status.label : undefined,
    businessType,
    dietaryType: config.showDietaryType ? dietaryType(product) : undefined,
    disabled: status.disabled,
    quantityInCart,
  };
}

