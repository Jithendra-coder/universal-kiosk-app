"use client";

import { useEffect } from "react";
import { AutoRecoveringState } from "@/components/ui/AutoRecoveringState";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard error caught by boundary:", error);
  }, [error]);

  return (
    <div style={{ padding: "40px 24px", maxWidth: "720px", margin: "0 auto" }}>
      <AutoRecoveringState
        title="Could not load Dashboard module"
        description={
          error.message ||
          "This dashboard section encountered an unexpected error. It will automatically reload once connectivity is verified."
        }
        onRetry={reset}
      />
    </div>
  );
}
