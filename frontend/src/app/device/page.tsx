import { Suspense } from "react";
import { DeviceApp } from "@/features/device/DeviceApp";

export default function DevicePage() { return <Suspense fallback={<main className="counter-auth"><p>Securing device session…</p></main>}><DeviceApp /></Suspense>; }
