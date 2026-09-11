"use client";

import { useRef, type ComponentPropsWithoutRef, type CSSProperties, type KeyboardEvent, type ReactNode } from "react";
import { cn } from "@/lib/utils";

type DivProps = ComponentPropsWithoutRef<"div">;

export function PageContainer({ className, width = "standard", ...props }: DivProps & { width?: "compact" | "standard" | "wide" | "maximum" | "analytics" | "form" | "full" }) {
  return <div className={cn("mt-page-container", `mt-page-container--${width}`, className)} {...props} />;
}

export function PageHeader({ title, subtitle, description, eyebrow, meta, actions, overflow, className, ...props }: DivProps & { title: ReactNode; subtitle?: ReactNode; description?: ReactNode; eyebrow?: ReactNode; meta?: ReactNode; actions?: ReactNode; overflow?: ReactNode }) {
  return <header className={cn("mt-page-header", className)} {...props}><div className="mt-page-header__copy">{eyebrow && <p className="mt-page-header__eyebrow">{eyebrow}</p>}<h1 className="mt-type-page-heading">{title}</h1>{(description || subtitle) && <p className="mt-type-page-subtitle">{description || subtitle}</p>}{meta && <div className="mt-page-header__meta">{meta}</div>}</div>{(actions || overflow) && <div className="mt-page-header__actions">{actions}{overflow}</div>}</header>;
}

export function SectionHeader({ title, description, actions, level = 2, className, ...props }: DivProps & { title: ReactNode; description?: ReactNode; actions?: ReactNode; level?: 2 | 3 }) {
  const Heading = level === 2 ? "h2" : "h3";
  return <div className={cn("mt-section-header", className)} {...props}><div><Heading className={level === 2 ? "mt-type-section-heading" : "mt-type-subsection-heading"}>{title}</Heading>{description && <p className="mt-type-card-description">{description}</p>}</div>{actions && <div className="mt-section-header__actions">{actions}</div>}</div>;
}

export function Stack({ className, gap = 16, style, ...props }: DivProps & { gap?: 4 | 8 | 12 | 16 | 20 | 24 | 32 | 40 | 48 | 64 }) {
  return <div className={cn("mt-stack", className)} style={{ "--mt-stack-gap": `${gap}px`, ...style } as CSSProperties} {...props} />;
}

export function FilterBar({ children, actions, className, ...props }: DivProps & { actions?: ReactNode }) {
  return <div className={cn("mt-filter-bar", className)} {...props}><div className="mt-filter-bar__controls">{children}</div>{actions && <div className="mt-filter-bar__actions">{actions}</div>}</div>;
}

export function Tabs<T extends string>({ value, tabs, onChange, label = "Sections" }: { value: T; tabs: ReadonlyArray<{ value: T; label: string; disabled?: boolean }>; onChange: (value: T) => void; label?: string }) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const move = (index: number) => { const next = tabs[index]; if (next && !next.disabled) { onChange(next.value); refs.current[index]?.focus(); } };
  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => { const available = tabs.map((tab, tabIndex) => ({ tab, tabIndex })).filter(({ tab }) => !tab.disabled).map(({ tabIndex }) => tabIndex); const current = available.indexOf(index); if (event.key === "Home") { event.preventDefault(); move(available[0]); } else if (event.key === "End") { event.preventDefault(); move(available.at(-1) ?? index); } else if (event.key === "ArrowRight" || event.key === "ArrowDown") { event.preventDefault(); move(available[(current + 1) % available.length]); } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") { event.preventDefault(); move(available[(current - 1 + available.length) % available.length]); } };
  return <div className="mt-tabs" role="tablist" aria-label={label}>{tabs.map((tab, index) => <button ref={(element) => { refs.current[index] = element; }} type="button" role="tab" key={tab.value} aria-selected={value === tab.value} tabIndex={value === tab.value ? 0 : -1} disabled={tab.disabled} onKeyDown={(event) => onKeyDown(event, index)} onClick={() => onChange(tab.value)}>{tab.label}</button>)}</div>;
}
