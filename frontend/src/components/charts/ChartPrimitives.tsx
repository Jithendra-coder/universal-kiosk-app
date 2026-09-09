"use client";

import { useId, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export const CHART_COLORS = {
  sales: "#0B57F0", orders: "#0E9384", discounts: "#EAAA08", refunds: "#D92D20", comparison: "#7A5AF8", secondary: "#475467", positive: "#079455", grid: "#EAECF0",
} as const;

type Point = number | { label?: string; value: number; comparison?: number };

function points(values: ReadonlyArray<Point>) { return values.map((point, index) => typeof point === "number" ? { label: String(index + 1), value: point } : { label: point.label || String(index + 1), value: point.value, comparison: point.comparison }); }

export function ChartCard({ title, description, children, className }: { title?: ReactNode; description?: ReactNode; children: ReactNode; className?: string }) {
  return <article className={cn("mt-card", "mt-card--chart", "mt-chart-card", className)}>{(title || description) && <header className="mt-card-header"><div>{title && <h2>{title}</h2>}{description && <p>{description}</p>}</div></header>}{children}</article>;
}

export function ChartLegend({ items }: { items: ReadonlyArray<{ label: string; color: string }> }) { return <div className="mt-chart-legend" aria-label="Chart legend">{items.map((item) => <span key={item.label}><i style={{ backgroundColor: item.color }} aria-hidden="true" />{item.label}</span>)}</div>; }

export function EmptyChart({ title = "No chart data", description = "There is no data for this period." }: { title?: ReactNode; description?: ReactNode }) { return <div className="mt-chart-empty" role="status"><strong>{title}</strong><span>{description}</span></div>; }

export function LineChart({ values, color = CHART_COLORS.sales, comparison = false, ariaLabel = "Line chart", onPointSelect }: { values: ReadonlyArray<Point>; color?: string; comparison?: boolean; ariaLabel?: string; onPointSelect?: (point: { label: string; value: number }) => void }) {
  const id = useId(); const data = points(values); if (!data.length || data.every((point) => point.value === 0 && (!point.comparison || point.comparison === 0))) return <EmptyChart />;
  const max = Math.max(1, ...data.flatMap((point) => [point.value, point.comparison || 0])); const width = 640; const height = 220; const padX = 28; const padY = 20; const x = (index: number) => padX + (index * (width - padX * 2)) / Math.max(1, data.length - 1); const y = (value: number) => height - padY - (value / max) * (height - padY * 2); const path = (key: "value" | "comparison") => data.map((point, index) => `${index ? "L" : "M"}${x(index).toFixed(1)},${y(point[key] || 0).toFixed(1)}`).join(" "); const highest = data.reduce((best, point) => point.value > best.value ? point : best, data[0]); const lowest = data.reduce((best, point) => point.value < best.value ? point : best, data[0]); const trend = data.at(-1)!.value >= data[0].value ? "upward" : "downward"; const summary = `Highest ${highest.label}: ${highest.value}. Lowest ${lowest.label}: ${lowest.value}. Trend is ${trend}.`;
  return <div className="mt-chart" role="img" aria-label={ariaLabel} aria-describedby={id}><svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none"><title>{summary}</title>{[0, .25, .5, .75, 1].map((ratio) => <line key={ratio} x1={padX} x2={width - padX} y1={y(max * ratio)} y2={y(max * ratio)} stroke={CHART_COLORS.grid} strokeWidth="1" />)}<path d={path("value")} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="mt-chart-line" />{comparison && data.some((point) => typeof point.comparison === "number") && <path d={path("comparison")} fill="none" stroke={CHART_COLORS.comparison} strokeWidth="2" strokeDasharray="5 5" />}{data.map((point, index) => <circle key={`${point.label}-${index}`} cx={x(index)} cy={y(point.value)} r="4" fill={color} tabIndex={onPointSelect ? 0 : undefined} role={onPointSelect ? "button" : undefined} aria-label={onPointSelect ? `${point.label}: ${point.value}` : undefined} onClick={() => onPointSelect?.({ label: point.label, value: point.value })} onKeyDown={(event) => { if (onPointSelect && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); onPointSelect({ label: point.label, value: point.value }); } }}><title>{`${point.label}: ${point.value}`}</title></circle>)}<g className="mt-chart-axis-labels">{data.map((point, index) => <text key={`${point.label}-axis`} x={x(index)} y={height - 2} textAnchor="middle">{point.label}</text>)}</g></svg><p id={id} className="mt-chart-summary">{summary}</p>{comparison && <ChartLegend items={[{ label: "Current", color }, { label: "Comparison", color: CHART_COLORS.comparison }]} />}</div>;
}

