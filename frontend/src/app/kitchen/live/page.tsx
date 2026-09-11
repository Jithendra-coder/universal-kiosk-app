import { Suspense } from "react";
import { KitchenApp } from "@/features/kitchen/KitchenApp";
import { KitchenDisplaySkeleton } from "@/components/ui/Skeletons";

export default function KitchenLivePage() { return <Suspense fallback={<KitchenDisplaySkeleton />}><KitchenApp /></Suspense>; }
