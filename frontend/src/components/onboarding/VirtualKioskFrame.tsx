"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import type { KioskScreenOrientation } from "@/lib/types";

const VIRTUAL_SCREENS = {
  portrait: { width: 1080, height: 1920 },
  landscape: { width: 1920, height: 1080 },
} as const;

export function VirtualKioskFrame({
  orientation = "portrait",
  interactive = false,
  size = "preview",
  label,
  children,
}: {
  orientation?: KioskScreenOrientation;
  interactive?: boolean;
  size?: "preview" | "test";
  label: string;
  children: ReactNode;
}) {
  const frameRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0);
  const screen = VIRTUAL_SCREENS[orientation];

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    const resize = () => setScale(Math.min(frame.clientWidth / screen.width, frame.clientHeight / screen.height));
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [screen.height, screen.width]);

  return (
    <div
      ref={frameRef}
      className={`mt-virtual-kiosk-frame mt-virtual-kiosk-frame--${size}`}
      data-orientation={orientation}
      data-virtual-width={screen.width}
      data-virtual-height={screen.height}
      aria-label={label}
    >
      <div
        className="mt-virtual-kiosk-frame__viewport"
        style={{
          width: screen.width * scale,
          height: screen.height * scale,
        }}
      >
        <div
          className="mt-virtual-kiosk-frame__screen"
          inert={!interactive}
          style={{
            width: screen.width,
            height: screen.height,
            transform: `scale(${scale})`,
          }}
        >
          {children}
        </div>
        {!interactive && <span className="mt-virtual-kiosk-frame__lock" aria-hidden="true" />}
      </div>
    </div>
  );
}
