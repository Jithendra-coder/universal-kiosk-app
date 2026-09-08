import type { Business, KioskStartScreenSettings } from "@/lib/types";

type SupportedStartType =
  | "grocery"
  | "salon"
  | "cafe"
  | "pizza"
  | "burger"
  | "restaurant"
  | "retail"
  | "pharmacy"
  | "bakery"
  | "cinema"
  | "ice_cream"
  | "other";

type KioskStartCopyInput = Pick<Business, "name" | "type" | "offer_title" | "offer_subtitle" | "offer_badge">;
type KioskStartSettingsInput = Pick<KioskStartScreenSettings, "welcome_text" | "instruction_text"> & { highlight_text?: string; start_prompt?: string } | null | undefined;

const SUPPORTED_START_TYPES = new Set<SupportedStartType>(["grocery", "salon", "cafe", "pizza", "burger", "restaurant", "retail", "pharmacy", "bakery", "cinema", "ice_cream", "other"]);

const LEGACY_HEADLINE_DEFAULTS = new Set([
  "a faster way to order what you love.",
  "fresh choices, smart savings",
  "order here",
  "welcome, start fresh",
  "touch screen to order",
  "choose your service",
]);

const LEGACY_SUBTITLE_DEFAULTS = new Set([
  "browse the menu, customize your favorites, and place your order when you are ready.",
  "discover today's best picks and seasonal offers.",
  "order your favorites in seconds.",
  "today's fresh picks are ready",
]);

const LEGACY_INSTRUCTION_DEFAULTS = new Set(["start screen"]);

export function normalizeBusinessStartType(type?: string | null): SupportedStartType {
  const raw = (type ?? "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/[\s-]+/g, "_");

  if (raw === "retail_store") return "retail";
  if (raw === "icecream" || raw === "ice_creams") return "ice_cream";
  if (SUPPORTED_START_TYPES.has(raw as SupportedStartType)) return raw as SupportedStartType;
  return "other";
}

export function kioskStartCopy(business: KioskStartCopyInput, settings?: KioskStartSettingsInput) {
  const name = business.name?.trim() || "our store";
  const type = normalizeBusinessStartType(business.type);
  const customWelcomeText = settings?.highlight_text?.trim() || settings?.welcome_text?.trim();
  const customInstructionTextFromSettings = settings?.start_prompt?.trim() || settings?.instruction_text?.trim();
  const customLandingText = cleanCustomTexts(splitPersistedText(business.offer_title), LEGACY_HEADLINE_DEFAULTS)[0];
  const customInstructionText = cleanCustomTexts(splitPersistedText(business.offer_badge), LEGACY_INSTRUCTION_DEFAULTS)[0];
  const cleanCustomSubtitleTexts = cleanCustomTexts(splitPersistedText(business.offer_subtitle), LEGACY_SUBTITLE_DEFAULTS);
  const subtitleTexts = cleanCustomSubtitleTexts.length > 0 ? cleanCustomSubtitleTexts : [];

  return {
    businessType: type,
    businessName: name,
    welcomeText: customWelcomeText || `Welcome to ${name}`,
    landingText: customLandingText ?? "Order Here",
    instructionText: customInstructionTextFromSettings || customInstructionText || "Touch screen to order",
    subtitleTexts,
    subtitleKey: [type, name, subtitleTexts.join("|")].join(":"),
    hasCustomSubtitle: cleanCustomSubtitleTexts.length > 0,
  };
}

export function splitPersistedText(value?: string | null) {
  return (value ?? "").split(/\r?\n/g);
}

export function joinPersistedText(lines: string[]) {
  return cleanCustomTexts(lines).join("\n");
}

export function cleanStartScreenDraftValue(value: string | null | undefined, kind: "landing" | "instruction" | "subtitle") {
  const legacyDefaults = kind === "landing" ? LEGACY_HEADLINE_DEFAULTS : kind === "instruction" ? LEGACY_INSTRUCTION_DEFAULTS : LEGACY_SUBTITLE_DEFAULTS;
  const cleaned = cleanCustomTexts(splitPersistedText(value), legacyDefaults);
  return kind === "subtitle" ? cleaned.join("\n") : (cleaned[0] ?? "");
}

function cleanCustomTexts(texts: string[], legacyDefaults?: Set<string>) {
  return texts
    .map((text) => text.trim())
    .filter((text) => {
      if (!text) return false;
      if (legacyDefaults?.has(text.toLowerCase())) return false;
      return true;
    });
}
