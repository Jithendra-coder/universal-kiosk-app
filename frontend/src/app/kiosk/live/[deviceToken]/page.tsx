"use client";

import { useParams } from "next/navigation";
import { LiveDeviceBootstrap } from "@/app/device/_components/live-device-bootstrap";

export default function LiveKioskDevicePage() {
  const params = useParams<{ deviceToken: string }>();
  return <LiveDeviceBootstrap deviceToken={String(params.deviceToken ?? "")} expectedType="kiosk" />;
}
