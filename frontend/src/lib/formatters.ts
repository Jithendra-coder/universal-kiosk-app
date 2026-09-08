const labels: Record<string, string> = {
  pending: "Pending", payment_pending: "Payment pending", preparing: "Preparing", ready: "Ready",
  completed: "Completed", cancelled: "Cancelled", failed: "Failed", refunded: "Refunded",
  active: "Active", inactive: "Inactive", online: "Online", offline: "Offline", unavailable: "Unavailable",
  dine_in: "Dine-in", takeaway: "Takeaway", pickup: "Pickup", delivery: "Delivery",
};

export function formatCurrency(value: number | null | undefined, currency = "INR", locale?: string) {
  const normalized = ({ "₹": "INR", Rs: "INR", "Rs ": "INR", "$": "USD", "€": "EUR", "£": "GBP" } as Record<string, string>)[currency] || currency || "INR";
  return new Intl.NumberFormat(locale || "en-IN", { style: "currency", currency: normalized, maximumFractionDigits: 2 }).format(Number(value || 0));
}
export function formatNumber(value: number | null | undefined, locale?: string) { return new Intl.NumberFormat(locale || "en-IN", { maximumFractionDigits: 2 }).format(Number(value || 0)); }
export function formatInteger(value: number | null | undefined, locale?: string) { return new Intl.NumberFormat(locale || "en-IN", { maximumFractionDigits: 0 }).format(Number(value || 0)); }
export function formatDateTime(value?: string | Date | null, timezone?: string, locale?: string) {
  if (!value) return "—"; const date = value instanceof Date ? value : new Date(value); if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(locale || "en-IN", { dateStyle: "medium", timeStyle: "short", timeZone: timezone }).format(date);
}
export function formatDate(value?: string | Date | null, timezone?: string, locale?: string) {
  if (!value) return "—"; const date = value instanceof Date ? value : new Date(value); if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(locale || "en-IN", { dateStyle: "medium", timeZone: timezone }).format(date);
}
export function formatTime(value?: string | Date | null, timezone?: string, locale?: string) {
  if (!value) return "—"; const date = value instanceof Date ? value : new Date(value); if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(locale || "en-IN", { timeStyle: "short", timeZone: timezone }).format(date);
}
export function formatRelativeTime(value?: string | Date | null, now = Date.now()) {
  if (!value) return "—"; const date = value instanceof Date ? value : new Date(value); if (Number.isNaN(date.getTime())) return "—";
  const minutes = Math.round((date.getTime() - now) / 60000); const unit = Math.abs(minutes) < 60 ? "minute" : "hour"; const amount = unit === "minute" ? minutes : Math.round(minutes / 60);
  return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(amount, unit);
}
export function formatDuration(seconds: number | null | undefined) { const total = Math.max(0, Math.round(Number(seconds || 0))); const minutes = Math.floor(total / 60); return minutes ? `${minutes}m ${total % 60}s` : `${total}s`; }
export function labelFor(value?: string | null) { if (!value) return "—"; return labels[value.toLowerCase()] || value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
export const formatProductName = (value?: string | null) => value?.trim() || "Unnamed item";
export const formatCategoryName = (value?: string | null) => value?.trim() || "Uncategorised";
export const formatLocationName = (value?: string | null) => value?.trim() || "All locations";
export const formatDeviceStatus = labelFor;
export const formatOrderStatus = labelFor;
export const formatPaymentStatus = labelFor;
