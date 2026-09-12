"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";

/**
 * Probes the backend health endpoint to check if the site and API are operational.
 */
export async function checkSiteAvailability(timeoutMs = 3500): Promise<boolean> {
  if (typeof window === "undefined") return true;

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const healthUrl = `${API_BASE}/health`;
    const response = await fetch(healthUrl, {
      method: "GET",
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    window.clearTimeout(timer);
  }
}

export type AutoReconnectOptions = {
  isError: boolean;
  onReconnect: () => unknown | Promise<unknown>;
  intervalMs?: number;
  maxIntervalMs?: number;
  enabled?: boolean;
};

export type AutoReconnectState = {
  isReconnecting: boolean;
  retryCount: number;
  probeNow: () => Promise<boolean>;
};

/**
 * Hook that detects when the backend or network recovers and automatically
 * triggers the provided `onReconnect` callback without requiring manual interaction.
 */
export function useAutoReconnect({
  isError,
  onReconnect,
  intervalMs = 3000,
  maxIntervalMs = 8000,
  enabled = true,
}: AutoReconnectOptions): AutoReconnectState {
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const onReconnectRef = useRef(onReconnect);
  useEffect(() => {
    onReconnectRef.current = onReconnect;
  }, [onReconnect]);

  const inFlightRef = useRef(false);

  const attemptReconnect = useCallback(async (): Promise<boolean> => {
    if (inFlightRef.current) return false;
    inFlightRef.current = true;
    setIsReconnecting(true);

    try {
      const isAvailable = await checkSiteAvailability(3500);
      if (isAvailable) {
        setRetryCount(0);
        await onReconnectRef.current();
        return true;
      }
      setRetryCount((prev) => prev + 1);
      return false;
    } catch {
      setRetryCount((prev) => prev + 1);
      return false;
    } finally {
      setIsReconnecting(false);
      inFlightRef.current = false;
    }
  }, []);

  useEffect(() => {
    if (!enabled || !isError || typeof window === "undefined") {
      return;
    }

    // 1. Listen for browser network restoration
    const handleOnline = () => {
      void attemptReconnect();
    };

    // 2. Listen for tab focus / visibility
    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        void attemptReconnect();
      }
    };

    window.addEventListener("online", handleOnline);
    document.addEventListener("visibilitychange", handleVisibility);

    // 3. Periodic probe with backoff and small jitter
    let timeoutId: number;
    let isActive = true;

    const scheduleNextProbe = (attempt: number) => {
      if (!isActive) return;
      const delay = Math.min(intervalMs * Math.pow(1.3, attempt), maxIntervalMs) + Math.random() * 500;
      timeoutId = window.setTimeout(async () => {
        if (!isActive) return;
        const recovered = await attemptReconnect();
        if (!recovered && isActive) {
          scheduleNextProbe(attempt + 1);
        }
      }, delay);
    };

    scheduleNextProbe(retryCount);

    return () => {
      isActive = false;
      window.clearTimeout(timeoutId);
      window.removeEventListener("online", handleOnline);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [attemptReconnect, enabled, intervalMs, isError, maxIntervalMs, retryCount]);

  return {
    isReconnecting,
    retryCount,
    probeNow: attemptReconnect,
  };
}
