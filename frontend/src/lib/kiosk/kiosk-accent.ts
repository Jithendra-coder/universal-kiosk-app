import type { CSSProperties } from "react";

export const DEFAULT_KIOSK_ACCENT = "#6D5DFB";
export const KIOSK_MULTI_ACCENT = "multi";
export const KIOSK_MULTI_ACCENT_FALLBACK = "#0F172A";

export const KIOSK_ACCENT_PRESETS = [
  { label: "Sky Blue", value: "#0284C7" },
  { label: "Red", value: "#DC2626" },
  { label: "Purple", value: "#7C3AED" },
  { label: "Rose", value: "#E11D48" },
  { label: "Indigo", value: "#4F46E5" },
  { label: "Yellow", value: "#EAB308" },
  { label: "Lime", value: "#65A30D" },
  { label: "Pink", value: "#DB2777" },
  { label: "Amber", value: "#D97706" },
  { label: "Emerald", value: "#059669" },
  { label: "Orange", value: "#EA580C" },
] as const;

export function normalizeKioskAccent(value?: string | null) {
  if (isKioskMultiAccent(value)) return KIOSK_MULTI_ACCENT;
  const color = String(value ?? "").trim().toUpperCase();
  return /^#[0-9A-F]{6}$/.test(color) ? color : DEFAULT_KIOSK_ACCENT;
}

export function isKioskMultiAccent(value?: string | null) {
  const accent = String(value ?? "").trim().toLowerCase();
  return accent === KIOSK_MULTI_ACCENT || accent === "rainbow" || accent === "multi-color" || accent === "multicolor";
}

export function resolveKioskAccentColor(value?: string | null) {
  const accent = normalizeKioskAccent(value);
  return accent === KIOSK_MULTI_ACCENT ? KIOSK_MULTI_ACCENT_FALLBACK : accent;
}

export function kioskAccentStyle(value?: string | null, primaryValue?: string | null): CSSProperties {
  const accent = resolveKioskAccentColor(value);
  const primary = resolveKioskAccentColor(primaryValue ?? accent);
  const foreground = readableForeground(accent);
  const primaryForeground = readableForeground(primary);
  return {
    "--kiosk-primary": primary,
    "--kiosk-primary-foreground": primaryForeground,
    "--kiosk-accent": accent,
    "--kiosk-accent-foreground": foreground,
    "--kiosk-accent-hover": mixHex(accent, "#000000", 0.12),
    "--kiosk-accent-soft": mixHex(accent, "#FFFFFF", 0.88),
    "--kiosk-accent-ring": hexToRgba(accent, 0.28),
  } as CSSProperties;
}

function readableForeground(hex: string) {
  const [red, green, blue] = hexToRgb(hex).map((channel) => {
    const normalized = channel / 255;
    return normalized <= 0.03928
      ? normalized / 12.92
      : Math.pow((normalized + 0.055) / 1.055, 2.4);
  });
  const luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
  return luminance > 0.46 ? "#111827" : "#FFFFFF";
}

function mixHex(base: string, target: string, amount: number) {
  const baseRgb = hexToRgb(base);
  const targetRgb = hexToRgb(target);
  const mixed = baseRgb.map((channel, index) =>
    Math.round(channel + (targetRgb[index] - channel) * amount)
  );
  return `#${mixed.map((channel) => channel.toString(16).padStart(2, "0")).join("").toUpperCase()}`;
}

function hexToRgba(hex: string, alpha: number) {
  const [red, green, blue] = hexToRgb(hex);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function hexToRgb(hex: string) {
  return [
    Number.parseInt(hex.slice(1, 3), 16),
    Number.parseInt(hex.slice(3, 5), 16),
    Number.parseInt(hex.slice(5, 7), 16),
  ];
}
