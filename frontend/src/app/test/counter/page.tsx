"use client";

import { Suspense } from "react";
import { CounterApp } from "@/features/counter/CounterApp";

export default function TestCounterPage() {
  return <Suspense fallback={<main className="staff-recovery"><p>Loading Test Counter…</p></main>}><CounterApp runtimeMode="test" /></Suspense>;
}
