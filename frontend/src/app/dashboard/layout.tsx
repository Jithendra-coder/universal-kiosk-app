import type { ReactNode } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { BusinessProvider } from "@/components/layout/BusinessProvider";
import { ProtectedRouteGate } from "@/components/layout/ProtectedRouteGate";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <BusinessProvider><ProtectedRouteGate area="dashboard"><AppShell>{children}</AppShell></ProtectedRouteGate></BusinessProvider>;
}
