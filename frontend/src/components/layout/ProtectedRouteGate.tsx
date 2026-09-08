"use client";

import { useEffect, useMemo, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useBusiness } from "@/components/layout/BusinessProvider";
import { safeSetupRoute } from "@/lib/protected-routing";

type ProtectedArea = "dashboard" | "setup";

export function ProtectedRouteGate({ area, children }: { area: ProtectedArea; children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { loading, error, refresh, onboardingStatus, onboardingLoading, onboardingError, refreshOnboarding } = useBusiness();
  const unresolved = loading || onboardingLoading;
  const loadError = error || onboardingError;
  const redirectTarget = useMemo(() => {
    if (unresolved || loadError || !onboardingStatus) return null;
    if (area === "dashboard" && !onboardingStatus.onboarding_completed) return safeSetupRoute(onboardingStatus.next_route);
    if (area === "setup" && onboardingStatus.onboarding_completed) {
      return pathname === "/setup/test-kiosk" ? "/dashboard/kiosk-experience/publish?test=1" : "/dashboard";
    }
    return null;
  }, [area, loadError, onboardingStatus, pathname, unresolved]);

  useEffect(() => {
    if (redirectTarget) router.replace(redirectTarget);
  }, [redirectTarget, router]);

  if (unresolved || redirectTarget) return <div className="mt-page-loading" role="status">Loading your workspace…</div>;
  if (loadError || !onboardingStatus) return <div className="mt-card mt-state-card" role="alert"><strong>Could not verify your workspace.</strong><p>{loadError || "Onboarding status is unavailable."}</p><button className="mt-button mt-button--secondary" type="button" onClick={() => void Promise.all([refresh(), refreshOnboarding()])}>Try again</button></div>;
  return children;
}
