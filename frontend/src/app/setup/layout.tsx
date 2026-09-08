import type { ReactNode } from "react";
import { AmbientBackground } from "@/components/AmbientBackground";
import { BusinessProvider } from "@/components/layout/BusinessProvider";
import { ProtectedRouteGate } from "@/components/layout/ProtectedRouteGate";
import { MenuPresetExperienceProvider } from "@/features/onboarding/menu-presets";

export default function SetupLayout({ children }: { children: ReactNode }) {
  return (
    <BusinessProvider>
      <ProtectedRouteGate area="setup">
        <MenuPresetExperienceProvider>
          <div className="mt-setup-layout">
            <AmbientBackground />
            <div className="mt-setup-layout__content">{children}</div>
          </div>
        </MenuPresetExperienceProvider>
      </ProtectedRouteGate>
    </BusinessProvider>
  );
}
