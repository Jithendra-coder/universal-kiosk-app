"use client";

import { useEffect } from "react";
import { AutoRecoveringState } from "@/components/ui/AutoRecoveringState";

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Root application error boundary caught:", error);
  }, [error]);

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "24px",
        background: "#f8fafc",
      }}
    >
      <div style={{ width: "100%", maxWidth: "560px" }}>
        <AutoRecoveringState
          title="Something went wrong"
          description={
            error.message ||
            "An unexpected error occurred while loading this page. The system will automatically attempt recovery when the connection is available."
          }
          onRetry={reset}
        />
      </div>
    </main>
  );
}
