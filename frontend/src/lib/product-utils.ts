import type { Product } from "@/lib/types";

export function discountActive(product: Product) {
  if (!product.discount_type || product.discount_type === "none") return false;
  if (!Number(product.discount_value)) return false;
  const now = Date.now();
  const starts = product.discount_starts_at ? new Date(product.discount_starts_at).getTime() : null;
  const ends = product.discount_ends_at ? new Date(product.discount_ends_at).getTime() : null;
  if (starts && now < starts) return false;
  if (ends && now > ends) return false;
  return true;
}

export function effectivePrice(product: Product) {
  const price = Number(product.price || 0);
  if (!discountActive(product)) return price;
  const value = Number(product.discount_value || 0);
  if (product.discount_type === "percentage") {
    return Math.max(price - (price * Math.min(value, 100)) / 100, 0);
  }
  if (product.discount_type === "fixed") {
    return Math.max(price - value, 0);
  }
  return price;
}

export function discountBadge(product: Product) {
  if (!discountActive(product)) return null;
  if (product.discount_label) return product.discount_label;
  if (product.discount_type === "percentage") return `${Number(product.discount_value)}% off`;
  if (product.discount_type === "fixed") return "Deal";
  return null;
}
