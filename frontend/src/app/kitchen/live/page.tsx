import { Suspense } from "react";
import { KitchenApp } from "@/features/kitchen/KitchenApp";

export default function KitchenLivePage() { return <Suspense fallback={<main className="staff-recovery"><p>Loading Kitchen…</p></main>}><KitchenApp /></Suspense>; }
