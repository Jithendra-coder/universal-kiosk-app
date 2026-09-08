"use client";

import { Suspense } from "react";
import { KitchenApp } from "@/features/kitchen/KitchenApp";

export default function TestKitchenPage() {
  return <Suspense fallback={<main className="staff-recovery"><p>Loading Test Kitchen…</p></main>}><KitchenApp runtimeMode="test" /></Suspense>;
}
