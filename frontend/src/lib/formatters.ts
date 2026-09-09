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
export function formatDateTime(value?: string | Date | null, timezone?: string, locale?: string) {
  if (!value) return "—"; const date = value instanceof Date ? value : new Date(value); if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(locale || "en-IN", { dateStyle: "medium", timeStyle: "short", timeZone: timezone }).format(date);
}
export function formatDuration(seconds: number | null | undefined) { const total = Math.max(0, Math.round(Number(seconds || 0))); const minutes = Math.floor(total / 60); return minutes ? `${minutes}m ${total % 60}s` : `${total}s`; }
export function labelFor(value?: string | null) { if (!value) return "—"; return labels[value.toLowerCase()] || value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
export const formatCategoryName = (value?: string | null) => value?.trim() || "Uncategorised";
export const formatOrderStatus = labelFor;
export const formatPaymentStatus = labelFor;
