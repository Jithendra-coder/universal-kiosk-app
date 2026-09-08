"use client";

import { useEffect, useId, useMemo, useRef, useState, type ButtonHTMLAttributes, type InputHTMLAttributes, type KeyboardEvent as ReactKeyboardEvent, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "tertiary" | "danger" | "ghost" | "icon"; loading?: boolean; permissionRestricted?: boolean };

export function Button({ className, variant = "primary", loading, permissionRestricted, disabled, children, title, ...props }: ButtonProps) {
  return <button className={cn("mt-button", `mt-button--${variant}`, className)} disabled={disabled || loading || permissionRestricted} aria-busy={loading || undefined} title={permissionRestricted ? "You do not have permission to use this action" : title} {...props}><span className="mt-button__label">{children}</span>{loading && <span className="mt-spinner" aria-hidden="true" />}</button>;
}

export function IconButton({ className, variant = "ghost", children, ...props }: Omit<ButtonProps, "aria-label"> & { "aria-label": string }) {
  return <Button className={cn("mt-icon-button", className)} variant={variant} {...props}>{children}</Button>;
}

function Field({ id, label, helperText, error, required, children }: { id: string; label: ReactNode; helperText?: ReactNode; error?: ReactNode; required?: boolean; children: ReactNode }) {
  const messageId = `${id}-message`;
  return <label className="mt-field" htmlFor={id}><span className="mt-field__label">{label}{required && <><span aria-hidden="true"> *</span><span className="mt-sr-only"> required</span></>}</span>{children}{(error || helperText) && <span id={messageId} className={cn("mt-field__message", Boolean(error) && "mt-field__message--error")}>{error || helperText}</span>}</label>;
}

export function Input({ label, helperText, error, className, id: suppliedId, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: ReactNode; helperText?: ReactNode; error?: ReactNode }) {
  const generatedId = useId(); const id = suppliedId || generatedId; const describedBy = error || helperText ? `${id}-message` : undefined;
  return <Field id={id} label={label} helperText={helperText} error={error} required={props.required}><input id={id} className={cn("mt-input", className)} aria-invalid={Boolean(error) || undefined} aria-describedby={describedBy} {...props} /></Field>;
}

export function SearchInput({ label = "Search", className, ...props }: Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { label?: string }) {
  return <label className={cn("mt-search-input", className)}><span className="mt-sr-only">{label}</span><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg><input type="search" aria-label={label} {...props} /></label>;
}

export function Textarea({ label, helperText, error, className, id: suppliedId, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { label: ReactNode; helperText?: ReactNode; error?: ReactNode }) {
  const generatedId = useId(); const id = suppliedId || generatedId; const describedBy = error || helperText ? `${id}-message` : undefined;
  return <Field id={id} label={label} helperText={helperText} error={error} required={props.required}><textarea id={id} className={cn("mt-textarea", className)} aria-invalid={Boolean(error) || undefined} aria-describedby={describedBy} {...props} /></Field>;
}

export function Select({ label, helperText, error, className, id: suppliedId, children, ...props }: SelectHTMLAttributes<HTMLSelectElement> & { label: ReactNode; helperText?: ReactNode; error?: ReactNode }) {
  const generatedId = useId(); const id = suppliedId || generatedId; const describedBy = error || helperText ? `${id}-message` : undefined;
  return <Field id={id} label={label} helperText={helperText} error={error} required={props.required}><select id={id} className={cn("mt-select", className)} aria-invalid={Boolean(error) || undefined} aria-describedby={describedBy} {...props}>{children}</select></Field>;
}

export function MultiSelect(props: SelectHTMLAttributes<HTMLSelectElement> & { label: ReactNode; helperText?: ReactNode; error?: ReactNode }) {
  return <Select multiple {...props} />;
}

export function Checkbox({ label, className, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: ReactNode }) {
  return <label className={cn("mt-choice", className)}><input type="checkbox" {...props} /><span>{label}</span></label>;
}

export function RadioGroup<T extends string>({ legend, name, value, options, onChange, disabled }: { legend: ReactNode; name: string; value?: T; options: ReadonlyArray<{ value: T; label: ReactNode; disabled?: boolean }>; onChange?: (value: T) => void; disabled?: boolean }) {
  return <fieldset className="mt-radio-group" disabled={disabled}><legend>{legend}</legend>{options.map((option) => <label className="mt-choice" key={option.value}><input type="radio" name={name} value={option.value} checked={value === option.value} disabled={option.disabled} onChange={() => onChange?.(option.value)} /><span>{option.label}</span></label>)}</fieldset>;
}

export function Toggle({ label, className, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: ReactNode }) {
  return <label className={cn("mt-toggle", className)}><input type="checkbox" role="switch" {...props} /><span className="mt-toggle__track" aria-hidden="true" /><span>{label}</span></label>;
}

export function DateRangeControl({ label = "Date range", startLabel = "Start date", endLabel = "End date", startProps, endProps }: { label?: string; startLabel?: string; endLabel?: string; startProps?: Omit<InputHTMLAttributes<HTMLInputElement>, "type">; endProps?: Omit<InputHTMLAttributes<HTMLInputElement>, "type"> }) {
  return <fieldset className="mt-date-range"><legend>{label}</legend><Input type="date" label={startLabel} {...startProps} /><Input type="date" label={endLabel} {...endProps} /></fieldset>;
}

export function StatusPill({ status, children, className }: { status: "neutral" | "success" | "warning" | "danger" | "info"; children: ReactNode; className?: string }) {
  return <span className={cn("mt-status-pill", `mt-status-pill--${status}`, className)}><span aria-hidden="true" />{children}</span>;
}

export function StatusBadge({ status = "neutral", children, icon, className }: { status?: "neutral" | "info" | "success" | "warning" | "danger" | "purple" | "disabled"; children: ReactNode; icon?: ReactNode; className?: string }) {
  return <span className={cn("mt-status-pill", "mt-status-badge", `mt-status-pill--${status}`, className)}><span aria-hidden="true">{icon || ""}</span>{children}</span>;
}

export function SegmentedControl<T extends string>({ value, options, onChange, label = "View mode" }: { value: T; options: ReadonlyArray<{ value: T; label: ReactNode; disabled?: boolean }>; onChange: (value: T) => void; label?: string }) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const move = (index: number) => { const option = options[index]; if (option && !option.disabled) { onChange(option.value); refs.current[index]?.focus(); } };
  const onKeyDown = (event: ReactKeyboardEvent<HTMLButtonElement>, index: number) => { const available = options.map((option, optionIndex) => option.disabled ? -1 : optionIndex).filter((optionIndex) => optionIndex >= 0); const current = available.indexOf(index); if (event.key === "Home") { event.preventDefault(); move(available[0]); } else if (event.key === "End") { event.preventDefault(); move(available.at(-1) ?? index); } else if (event.key === "ArrowRight" || event.key === "ArrowDown") { event.preventDefault(); move(available[(current + 1) % available.length]); } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") { event.preventDefault(); move(available[(current - 1 + available.length) % available.length]); } };
  return <div className="mt-segmented-control" role="group" aria-label={label}>{options.map((option, index) => <button ref={(element) => { refs.current[index] = element; }} type="button" key={option.value} aria-pressed={value === option.value} tabIndex={value === option.value ? 0 : -1} disabled={option.disabled} onKeyDown={(event) => onKeyDown(event, index)} onClick={() => onChange(option.value)}>{option.label}</button>)}</div>;
}

export function MetricCard({ title, value, description, trend, className }: { title: ReactNode; value: ReactNode; description?: ReactNode; trend?: ReactNode; className?: string }) {
  const displayValue = title === "Items Sold" && value === "Available" ? "—" : value;
  const displayDescription = title === "Items Sold" && typeof description === "string" ? "Quantity from completed production orders." : description;
  return <article className={cn("mt-card", "mt-metric-card", className)}><h3 className="mt-type-card-title">{title}</h3><p className="mt-type-kpi-value">{displayValue}</p>{trend && <div className="mt-metric-card__trend">{trend}</div>}{displayDescription && <p className="mt-type-card-description">{displayDescription}</p>}</article>;
}

export function Card({ variant = "static", title, description, children, className, onClick }: { variant?: "static" | "interactive" | "metric" | "insight" | "configuration" | "chart"; title?: ReactNode; description?: ReactNode; children?: ReactNode; className?: string; onClick?: () => void }) {
  const Tag = onClick ? "button" : "article";
  return <Tag type={onClick ? "button" : undefined} className={cn("mt-card", `mt-card--${variant}`, onClick && "mt-card--clickable", className)} onClick={onClick}><>{title && <header className="mt-card-header"><div><h2>{title}</h2>{description && <p>{description}</p>}</div></header>}{children}</></Tag>;
}

export type DataTableColumn<T> = { key: string; header: ReactNode; cell: (row: T) => ReactNode; align?: "start" | "center" | "end" };

export function DataTable<T>({ columns, rows, rowKey, caption, emptyMessage = "No records found.", loading = false }: { columns: ReadonlyArray<DataTableColumn<T>>; rows: ReadonlyArray<T>; rowKey: (row: T) => string; caption: string; emptyMessage?: ReactNode; loading?: boolean }) {
  if (loading) return <Skeleton lines={5} label={`Loading ${caption}`} />;
  if (!rows.length) return <EmptyState title="No data" description={emptyMessage} />;
  return <div className="mt-data-table-wrap"><table className="mt-data-table"><caption className="mt-sr-only">{caption}</caption><thead><tr>{columns.map((column) => <th key={column.key} scope="col" data-align={column.align}>{column.header}</th>)}</tr></thead><tbody>{rows.map((row) => <tr key={rowKey(row)}>{columns.map((column) => <td key={column.key} data-label={typeof column.header === "string" ? column.header : undefined} data-align={column.align}>{normalizeTableValue(column.cell(row))}</td>)}</tr>)}</tbody></table></div>;
}

function normalizeTableValue(value: ReactNode) { return typeof value === "string" && value.toLowerCase() === "not returned" ? "—" : value; }

export function MobileRecordCard({ title, fields, actions }: { title: ReactNode; fields: ReadonlyArray<{ label: ReactNode; value: ReactNode }>; actions?: ReactNode }) {
  return <article className="mt-mobile-record-card"><h3>{title}</h3><dl>{fields.map((field, index) => <div key={index}><dt>{field.label}</dt><dd>{field.value}</dd></div>)}</dl>{actions && <div className="mt-mobile-record-card__actions">{actions}</div>}</article>;
}

export function Pagination({ page, pageCount, onPageChange, label = "Pagination" }: { page: number; pageCount: number; onPageChange: (page: number) => void; label?: string }) {
  return <nav className="mt-pagination" aria-label={label}><Button variant="secondary" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>Previous</Button><span>Page {page} of {pageCount}</span><Button variant="secondary" disabled={page >= pageCount} onClick={() => onPageChange(page + 1)}>Next</Button></nav>;
}

export function Skeleton({ lines = 3, label = "Loading" }: { lines?: number; label?: string }) {
  return <div className="mt-skeleton" role="status" aria-label={label}>{Array.from({ length: lines }, (_, index) => <span key={index} aria-hidden="true" />)}</div>;
}

export type DataStateKind = "initial-loading" | "partial-loading" | "refreshing" | "empty" | "filtered-empty" | "permission-denied" | "recoverable-error" | "fatal-error" | "offline" | "reconnecting" | "sync-failed" | "stale" | "info" | "success";

export function DataState({ kind, title, description, action }: { kind: DataStateKind; title: ReactNode; description?: ReactNode; action?: ReactNode }) {
  const isError = kind === "recoverable-error" || kind === "fatal-error" || kind === "sync-failed";
  return <div className={cn("mt-feedback-state", `mt-feedback-state--${kind}`)} role={isError ? "alert" : "status"}><strong>{title}</strong>{description && <p>{description}</p>}{action && <div>{action}</div>}</div>;
}

export function EmptyState({ title = "Nothing here yet", description, action }: { title?: ReactNode; description?: ReactNode; action?: ReactNode }) { return <DataState kind="empty" title={title} description={description} action={action} />; }
export function ErrorState({ title = "Unable to load this content", description, action }: { title?: ReactNode; description?: ReactNode; action?: ReactNode }) { return <DataState kind="recoverable-error" title={title} description={description} action={action} />; }
export function PermissionDeniedState({ title = "Access restricted", description = "You do not have permission to view this content.", action }: { title?: ReactNode; description?: ReactNode; action?: ReactNode }) { return <DataState kind="permission-denied" title={title} description={description} action={action} />; }

type OverlayProps = { open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; footer?: ReactNode; className?: string; confirmOnClose?: string; variant?: "drawer" | "sheet" | "dialog" };

export function DetailsDrawer({ open, onClose, title, children, footer, className, confirmOnClose, variant = "drawer" }: OverlayProps) {
  const dialogRef = useRef<HTMLDialogElement>(null); const titleId = useId(); const returnFocus = useRef<HTMLElement | null>(null);
  useEffect(() => { const dialog = dialogRef.current; if (!open) { returnFocus.current?.focus(); returnFocus.current = null; return; } if (dialog && !dialog.open) { returnFocus.current = document.activeElement as HTMLElement; dialog.showModal(); } }, [open]);
  useEffect(() => { if (!open) return; const handleEscape = (event: globalThis.KeyboardEvent) => { if (event.key === "Escape") { event.preventDefault(); if (!confirmOnClose || window.confirm(confirmOnClose)) onClose(); } }; window.addEventListener("keydown", handleEscape, true); return () => window.removeEventListener("keydown", handleEscape, true); }, [open, confirmOnClose, onClose]);
  useEffect(() => { if (!open) return; const dialog = dialogRef.current; if (!dialog) return; const handleTab = (event: globalThis.KeyboardEvent) => { if (event.key !== "Tab") return; const focusable = Array.from(dialog.querySelectorAll<HTMLElement>('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')); if (!focusable.length) return; const first = focusable[0]; const last = focusable[focusable.length - 1]; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } }; dialog.addEventListener("keydown", handleTab); return () => dialog.removeEventListener("keydown", handleTab); }, [open]);
  const close = () => { if (!confirmOnClose || window.confirm(confirmOnClose)) onClose(); };
  return open ? <dialog ref={dialogRef} className={cn("mt-overlay", `mt-overlay--${variant}`, className)} aria-labelledby={titleId} onKeyDown={(event) => { if (event.key === "Escape") { event.preventDefault(); close(); } }} onCancel={(event) => { event.preventDefault(); close(); }} onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}><div className="mt-overlay__panel"><header><h2 id={titleId}>{title}</h2><IconButton aria-label="Close" onClick={close}>×</IconButton></header><div className="mt-overlay__content">{children}</div>{footer && <footer>{footer}</footer>}</div></dialog> : null;
}

export function MobileSheet(props: Omit<OverlayProps, "variant">) { return <DetailsDrawer variant="sheet" {...props} />; }

export function ConfirmationDialog({ open, onClose, onConfirm, title, description, confirmLabel = "Confirm", destructive = false, loading = false }: { open: boolean; onClose: () => void; onConfirm: () => void; title: ReactNode; description: ReactNode; confirmLabel?: string; destructive?: boolean; loading?: boolean }) {
  return <DetailsDrawer open={open} onClose={onClose} title={title} variant="dialog" footer={<><Button variant="secondary" onClick={onClose}>Cancel</Button><Button variant={destructive ? "danger" : "primary"} loading={loading} onClick={onConfirm}>{confirmLabel}</Button></>}><p>{description}</p></DetailsDrawer>;
}

export function Toast({ status = "info", children, onDismiss }: { status?: "success" | "warning" | "danger" | "info"; children: ReactNode; onDismiss?: () => void }) {
  return <div className={cn("mt-toast", `mt-toast--${status}`)} role={status === "danger" ? "alert" : "status"}><span>{children}</span>{onDismiss && <IconButton aria-label="Dismiss notification" onClick={onDismiss}>×</IconButton>}</div>;
}

export function Tooltip({ content, children }: { content: ReactNode; children: ReactNode }) {
  const id = useId(); return <span className="mt-tooltip"><span aria-describedby={id}>{children}</span><span id={id} role="tooltip">{content}</span></span>;
}

export function FilterToolbar({ children, actions, onOpenFilters, className }: { children: ReactNode; actions?: ReactNode; onOpenFilters?: () => void; className?: string }) {
  return <div className={cn("mt-filter-bar", "mt-filter-toolbar", className)}><div className="mt-filter-bar__controls">{children}</div>{onOpenFilters && <Button variant="secondary" className="mt-filter-toolbar__mobile-trigger" onClick={onOpenFilters}>Filters</Button>}{actions && <div className="mt-filter-bar__actions">{actions}</div>}</div>;
}

export const FilterBar = FilterToolbar;
export const SectionError = ErrorState;

export function FormSection({ title, description, children, actions, className }: { title: ReactNode; description?: ReactNode; children: ReactNode; actions?: ReactNode; className?: string }) {
  return <section className={cn("mt-form-section", className)}><header><div><h2>{title}</h2>{description && <p>{description}</p>}</div>{actions}</header>{children}</section>;
}

export function StickyFormActions({ children, className }: { children: ReactNode; className?: string }) { return <div className={cn("mt-sticky-action-bar", "mt-sticky-form-actions", className)}>{children}</div>; }

export function UploadField({ label, accept, maxSize = 5 * 1024 * 1024, value, onChange, error, helperText, progress }: { label: ReactNode; accept?: string; maxSize?: number; value?: File | null; onChange?: (file: File | null) => void; error?: ReactNode; helperText?: ReactNode; progress?: number }) {
  const id = useId(); const inputRef = useRef<HTMLInputElement>(null); const [localError, setLocalError] = useState(""); const preview = useMemo(() => value && value.type.startsWith("image/") ? URL.createObjectURL(value) : "", [value]);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  const choose = (file?: File) => { if (!file) return; if (file.size > maxSize) { setLocalError(`File must be smaller than ${Math.round(maxSize / 1024 / 1024)} MB.`); return; } setLocalError(""); onChange?.(file); };
  return <div className="mt-upload-field"><span className="mt-field__label">{label}</span><button type="button" className="mt-upload-field__dropzone" onClick={() => inputRef.current?.click()} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); choose(event.dataTransfer.files[0]); }} aria-describedby={`${id}-message`}><input ref={inputRef} id={id} className="mt-sr-only" type="file" accept={accept} onChange={(event) => choose(event.target.files?.[0])} /><span>{value ? `Selected ${value.name}` : "Drop a file here or choose one"}</span>{preview && <span className="mt-upload-field__preview" style={{ backgroundImage: `url(${preview})` }} aria-label={`Preview of ${value?.name}`} />}{typeof progress === "number" && <progress max="100" value={progress} aria-label="Upload progress" />}</button><span id={`${id}-message`} className={cn("mt-field__message", Boolean(error || localError) && "mt-field__message--error")}>{error || localError || helperText || "PNG, JPG or SVG. File paths are never shown."}</span>{value && <Button type="button" variant="tertiary" onClick={() => onChange?.(null)}>Remove file</Button>}</div>;
}

export function CommandPalette({ open, onClose, commands }: { open: boolean; onClose: () => void; commands: ReadonlyArray<{ label: string; onSelect: () => void }>; }) {
  const [query, setQuery] = useState(""); const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => { if (open) inputRef.current?.focus(); }, [open]);
  if (!open) return null;
  const filtered = commands.filter((command) => command.label.toLowerCase().includes(query.toLowerCase()));
  return <div className="mt-command-palette" role="dialog" aria-modal="true" aria-label="Command search" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><div className="mt-command-palette__panel"><label className="mt-field"><span className="mt-field__label">Search commands</span><input ref={inputRef} className="mt-input mt-command-palette__input" value={query} onChange={(event) => setQuery(event.target.value)} autoComplete="off" /></label>{filtered.length ? <div role="listbox">{filtered.map((command) => <button type="button" key={command.label} onClick={() => { command.onSelect(); onClose(); }}>{command.label}</button>)}</div> : <EmptyState title="No commands found" />}</div></div>;
}
