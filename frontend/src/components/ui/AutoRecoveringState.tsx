"use client";

import { type ReactNode } from "react";
import { useAutoReconnect } from "@/lib/connectivity";

export type AutoRecoveringStateProps = {
  title?: ReactNode;
  description?: ReactNode;
  onRetry: () => unknown | Promise<unknown>;
  action?: ReactNode;
  className?: string;
  compact?: boolean;
};

export function AutoRecoveringState({
  title = "Unable to connect to service",
  description = "The application could not reach the server. It will automatically reload as soon as the connection is restored.",
  onRetry,
  action,
  className = "",
  compact = false,
}: AutoRecoveringStateProps) {
  const { isReconnecting, retryCount, probeNow } = useAutoReconnect({
    isError: true,
    onReconnect: onRetry,
  });

  return (
    <div
      className={`mt-feedback-state mt-feedback-state--recoverable-error ${compact ? "mt-feedback-state--compact" : ""} ${className}`}
      role="alert"
      aria-live="polite"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        gap: "12px",
        padding: compact ? "16px 20px" : "28px 24px",
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          width: "44px",
          height: "44px",
          borderRadius: "12px",
          background: "#fee4e2",
          color: "#d92d20",
          fontSize: "20px",
          fontWeight: 700,
        }}
        aria-hidden="true"
      >
        !
      </div>

      <div>
        <strong style={{ display: "block", fontSize: compact ? "15px" : "17px", color: "var(--mt-text-primary, #101828)" }}>
          {title}
        </strong>
        {description && (
          <p
            style={{
              margin: "6px 0 0",
              maxWidth: "520px",
              fontSize: "13px",
              lineHeight: "20px",
              color: "var(--mt-text-secondary, #475467)",
            }}
          >
            {description}
          </p>
        )}
      </div>

      {/* Auto-reconnect live status indicator */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
          padding: "6px 14px",
          borderRadius: "999px",
          background: isReconnecting ? "#eff8ff" : "#fef3f2",
          border: `1px solid ${isReconnecting ? "#b2ddff" : "#fecdca"}`,
          color: isReconnecting ? "#175cd3" : "#b42318",
          fontSize: "12px",
          fontWeight: 600,
        }}
      >
        <span
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: isReconnecting ? "#155eef" : "#f04438",
            animation: "mt-pulse 1.4s ease-in-out infinite",
          }}
          aria-hidden="true"
        />
        {isReconnecting
          ? "Checking connection with server…"
          : retryCount > 0
          ? `Auto-reloading when available (checked ${retryCount} time${retryCount === 1 ? "" : "s"})`
          : "Auto-reloading when connection returns…"}
      </div>

      <div style={{ display: "flex", gap: "10px", marginTop: "4px" }}>
        {action}
        <button
          type="button"
          className="mt-button mt-button--secondary"
          onClick={() => void probeNow()}
          disabled={isReconnecting}
          style={{ cursor: isReconnecting ? "wait" : "pointer" }}
        >
          {isReconnecting ? "Connecting…" : "Try again now"}
        </button>
      </div>
    </div>
  );
}
