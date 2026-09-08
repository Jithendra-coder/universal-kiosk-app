import { Suspense } from "react";
import { CounterApp } from "@/features/counter/CounterApp";

export default function CounterLivePage() { return <Suspense fallback={<main className="staff-recovery"><p>Loading Counter…</p></main>}><CounterApp /></Suspense>; }
