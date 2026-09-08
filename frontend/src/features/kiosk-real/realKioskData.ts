// This file is real kiosk production runtime only. It must not import preview sandbox files.
import { api } from "@/lib/api";

export function loadRealKioskMenu(slug: string, locationId?: string | null) {
  return api.kioskMenu(slug, locationId);
}

export function loadDraftKioskMenu(businessId: string, locationId?: string | null) {
  return api.kioskDraftMenu(businessId, locationId);
}
