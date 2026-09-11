import { Suspense } from "react";
import { CounterApp } from "@/features/counter/CounterApp";
import { CounterPosSkeleton } from "@/components/ui/Skeletons";

export default function CounterLivePage() { return <Suspense fallback={<CounterPosSkeleton />}><CounterApp /></Suspense>; }
