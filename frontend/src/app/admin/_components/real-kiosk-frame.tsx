"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Maximize2 } from "lucide-react";
import type { KioskScreenOrientation } from "@/lib/types";

export type KioskFrameEvent = {
  source: "menutap-kiosk";
  version: 1;
  event: "kiosk-ready" | "category-selected" | "item-added" | "cart-opened" | "checkout-reached" | "test-payment-started" | "test-payment-completed" | "confirmation-shown" | "kiosk-error";
  kioskId: string;
  businessId: string;
  mode: "preview" | "test";
  sessionId: string;
  timestamp: string;
  payload?: Record<string, unknown>;
};

export function RealKioskFrame({ slug, businessId, locationId, orientation, mode = "preview", sessionKey = 0, onLoad, onKioskEvent, compact = false }: {
  slug: string;
  businessId?: string;
  locationId?: string | null;
  orientation: KioskScreenOrientation;
  mode?: "preview" | "test";
  sessionKey?: string | number;
  onLoad?: () => void;
  onKioskEvent?: (message: KioskFrameEvent) => void;
  compact?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const reactSessionId = useId();
  const sessionId = `frame-${reactSessionId.replace(/[^a-zA-Z0-9_-]/g, "")}-${mode}-${sessionKey}`;
  const seenEventsRef = useRef(new Set<string>());
  const [scale, setScale] = useState(1);
  const width = orientation === "portrait" ? 1080 : 1920;
  const height = orientation === "portrait" ? 1920 : 1080;

  useEffect(() => {
    seenEventsRef.current.clear();
  }, [sessionId]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const update = () => setScale(Math.min(container.clientWidth / width, container.clientHeight / height));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(container);
    return () => observer.disconnect();
  }, [height, width]);

  useEffect(() => {
    const receive = (event: MessageEvent) => {
      if (event.origin !== window.location.origin || event.source !== iframeRef.current?.contentWindow) return;
      const message = event.data as Partial<KioskFrameEvent> | null;
      if (!message || message.source !== "menutap-kiosk" || message.version !== 1 || message.kioskId !== slug || message.mode !== mode || message.sessionId !== sessionId || typeof message.businessId !== "string" || typeof message.timestamp !== "string" || typeof message.event !== "string") return;
      const typed = message as KioskFrameEvent;
      const requires: Partial<Record<KioskFrameEvent["event"], KioskFrameEvent["event"]>> = { "cart-opened": "item-added", "checkout-reached": "cart-opened", "test-payment-started": "checkout-reached", "test-payment-completed": "test-payment-started", "confirmation-shown": "test-payment-completed" };
      const prerequisite = requires[typed.event];
      if (prerequisite && !seenEventsRef.current.has(prerequisite)) return;
      seenEventsRef.current.add(typed.event);
      if (typed.event === "kiosk-ready") onLoad?.();
      onKioskEvent?.(typed);
    };
    window.addEventListener("message", receive);
    return () => window.removeEventListener("message", receive);
  }, [mode, onKioskEvent, onLoad, sessionId, slug]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3 text-xs font-semibold text-[var(--color-text-muted)]">
        <span>{width} × {height} · {Math.round(scale * 100)}%</span>
        <button type="button" onClick={() => void containerRef.current?.requestFullscreen()} className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-white px-3 font-semibold text-[var(--color-text-primary)] transition hover:bg-[var(--color-surface-hover)] active:bg-slate-100 focus-visible:ring-2 focus-visible:ring-[var(--color-focus-ring)]"><Maximize2 size={14} aria-hidden="true" /> Fullscreen</button>
      </div>
      <div ref={containerRef} className="relative mx-auto overflow-hidden rounded-xl border border-[var(--color-border)] bg-slate-100 shadow-sm" style={{ aspectRatio: `${width} / ${height}`, maxWidth: orientation === "portrait" ? (compact ? 236 : 405) : (compact ? 747 : 1280) }}>
        <iframe ref={iframeRef} key={`${mode}-${locationId || "all"}-${sessionKey}`} title={`${mode === "test" ? "Test" : "Preview"} kiosk`} src={`/kiosk/${encodeURIComponent(slug)}?mode=${mode}&embedded=1&session=${encodeURIComponent(sessionId)}${businessId ? `&business=${encodeURIComponent(businessId)}` : ""}${locationId ? `&location=${encodeURIComponent(locationId)}` : ""}`} className="absolute left-0 top-0 border-0 bg-white" style={{ width, height, transform: `scale(${scale})`, transformOrigin: "top left" }} />
      </div>
    </div>
  );
}
