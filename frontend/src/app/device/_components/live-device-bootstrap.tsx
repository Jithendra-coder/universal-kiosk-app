"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Loader2, MonitorSmartphone } from "lucide-react";
import { api } from "@/lib/api";
import type { LiveDeviceContext } from "@/lib/types";

type DeviceType = "kiosk" | "counter" | "kitchen";

const STORAGE_KEY = "menutap.device.session";

export function LiveDeviceBootstrap({ deviceToken, expectedType }: { deviceToken: string; expectedType: DeviceType }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const cleanPath = cleanLivePath(expectedType);

  useEffect(() => {
    let active = true;
    async function exchange() {
      try {
        const context = await api.exchangeLiveDeviceToken(deviceToken, expectedType);
        if (!active) return;
        saveDeviceSnapshot(context);
        router.replace(context.launch_path || cleanPath);
      } catch (err) {
        if (!active) return;
        try {
          window.localStorage.removeItem(STORAGE_KEY);
          await api.clearLiveDeviceSession().catch(() => undefined);
        } catch {
          // Storage/cookie cleanup is best effort before showing the repair path.
        }
        setError(err instanceof Error ? err.message : "This device link is invalid or disabled. Pair this device again.");
      }
    }
    void exchange();
    return () => {
      active = false;
    };
  }, [cleanPath, deviceToken, expectedType, router]);

  if (error) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#F7F8FB] px-5 text-[#0F172A]">
        <section className="w-full max-w-md rounded-lg border border-rose-200 bg-white p-6 text-center shadow-[0_18px_60px_rgba(15,23,42,0.10)]">
          <AlertTriangle className="mx-auto text-rose-600" size={32} />
          <h1 className="mt-4 text-2xl font-black">Device link unavailable</h1>
          <p className="mt-2 text-sm font-bold leading-6 text-[#64748B]">{error}</p>
          <button type="button" onClick={() => router.replace("/device/start")} className="mt-5 min-h-11 rounded bg-[#111827] px-5 text-sm font-black text-white">
            Pair this device
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[#F7F8FB] text-[#0F172A]">
      <div className="flex items-center gap-3 text-sm font-black text-[#64748B]">
        <span className="grid h-10 w-10 place-items-center rounded bg-white shadow-sm">
          <MonitorSmartphone size={18} />
        </span>
        <Loader2 className="animate-spin" size={18} />
        Securing device session
      </div>
    </main>
  );
}

export function saveDeviceSnapshot(context: LiveDeviceContext) {
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        device_type: context.device.device_type,
        launch_path: context.launch_path || cleanLivePath(context.device.device_type as DeviceType),
        device_id: context.device.id,
        device_name: context.device.name,
      })
    );
  } catch {
    // Snapshot is non-secret convenience only; the httpOnly cookie is authoritative.
  }
}

function cleanLivePath(deviceType: DeviceType | string) {
  if (deviceType === "counter") return "/device";
  if (deviceType === "kitchen") return "/device";
  return "/kiosk/live";
}
