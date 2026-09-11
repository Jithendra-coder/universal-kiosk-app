"use client";

import { useEffect } from "react";
import { AutoRecoveringState } from "@/components/ui/AutoRecoveringState";

export default function SetupError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Setup error caught by boundary:", error);
  }, [error]);

  return (
    <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "24px", background: "#f8fafc" }}>
      <div style={{ width: "100%", maxWidth: "560px" }}>
        <AutoRecoveringState
          title="Setup temporarily unavailable"
          description={
            error.message ||
            "We were unable to load the setup workspace. As soon as the service recovers, this step will reload automatically."
          }
          onRetry={reset}
        />
      </div>
    </main>
  );
}
