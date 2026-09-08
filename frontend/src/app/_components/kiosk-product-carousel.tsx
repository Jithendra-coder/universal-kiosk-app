"use client";

import { useState } from "react";
import Image from "next/image";
import { Minus, Package, Plus } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { money } from "@/lib/api";
import type { BusinessType } from "@/lib/types";
import type { KioskCardStyle, KioskProductDisplayStyle } from "@/lib/kiosk/kiosk-business-config";

export type KioskDietaryType = "veg" | "non_veg" | "egg" | "vegan";

export type KioskCarouselItem = {
  id: string | number;
  name: string;
  description?: string;
  imageUrl?: string;
  imageFit?: "cover" | "contain";
  price: number;
  priceLabel?: string;
  showPrice?: boolean;
  originalPrice?: number;
  discount?: string;
  metaLabel?: string;
  secondaryMetaLabel?: string;
  timeLabel?: string;
  statusLabel?: string;
  businessType?: BusinessType;
  dietaryType?: KioskDietaryType;
  disabled?: boolean;
  hideActions?: boolean;
  quantityInCart?: number;
};

type ProductActions = {
  onAdd: (item: KioskCarouselItem) => void;
  onIncrease: (item: KioskCarouselItem) => void;
  onDecrease: (item: KioskCarouselItem) => void;
};

export function KioskProductCard({
  item,
  currencySymbol,
  cardStyle = "detailed",
  displayStyle = "detailed_card",
  onAdd,
  onIncrease,
  onDecrease,
  className,
  density = "normal",
}: ProductActions & {
  item: KioskCarouselItem;
  businessType: BusinessType;
  currencySymbol: string;
  cardStyle?: Exclude<KioskCardStyle, "auto">;
  displayStyle?: KioskProductDisplayStyle;
  className?: string;
  density?: "normal" | "compact" | "landscape";
}) {
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);
  const dense = cardStyle === "fast_add";
  const compactCard = cardStyle === "compact";
  const imageFocused = cardStyle === "image_focused";
  const simple = displayStyle === "simple_item" || displayStyle === "dense_fast_add_list";
  const landscape = density === "landscape";
  const compactDensity = density === "compact" || landscape;
  const frameClass = landscape
    ? simple
      ? "grid-rows-[50%_1fr]"
      : imageFocused
        ? "grid-rows-[52%_1fr]"
        : compactCard || dense
          ? "grid-rows-[45%_1fr]"
          : "grid-rows-[48%_1fr]"
    : simple
      ? "grid-rows-[58%_1fr]"
      : imageFocused
        ? "grid-rows-[54%_1fr]"
        : compactCard || dense
          ? "grid-rows-[44%_1fr]"
          : "grid-rows-[48%_1fr]";
  const contentPaddingClass = landscape ? "px-3 pb-2.5 pt-4" : density === "compact" ? "px-2 pb-2 pt-3" : "px-4 pb-4 pt-5";
  const titleClass = landscape
    ? simple
      ? "text-[clamp(15px,1.12vw,20px)]"
      : "text-[clamp(15px,1.05vw,19px)]"
    : density === "compact"
      ? "text-[14px]"
      : simple
        ? "text-lg sm:text-xl"
        : "text-xl sm:text-2xl";
  const priceClass = landscape
    ? "text-[clamp(16px,1.12vw,22px)] leading-tight"
    : density === "compact"
      ? "text-[16px]"
      : simple
        ? "text-xl sm:text-2xl"
        : "text-2xl sm:text-[28px]";
  const actionButtonClass = landscape ? "h-10 w-[86px] rounded-xl" : density === "compact" ? "h-8 w-[68px] rounded-lg" : "h-12 w-[112px] rounded-2xl";
  const quantityGridClass = landscape ? "w-[86px] grid-cols-3 rounded-xl" : density === "compact" ? "w-[68px] grid-cols-3 rounded-lg" : "w-[112px] grid-cols-3 rounded-2xl";
  const quantityCellClass = landscape ? "h-9" : density === "compact" ? "h-7" : "h-12";
  const quantityTextClass = landscape ? "h-9 text-[13px]" : density === "compact" ? "h-7 text-[11px]" : "h-12 text-base";
  const dietaryColor =
    item.dietaryType === "non_veg"
      ? "border-rose-600 text-rose-600"
      : item.dietaryType === "egg"
        ? "border-amber-500 text-amber-600"
        : "border-emerald-600 text-emerald-700";

  return (
    <motion.article
      data-testid="kiosk-product-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "relative grid h-full min-h-0 overflow-hidden border border-slate-200 bg-white text-slate-950 shadow-[0_12px_28px_rgba(15,23,42,0.08)]",
        landscape ? "rounded-xl" : "rounded-2xl",
        frameClass,
        item.disabled && "opacity-70",
        className
      )}
    >
      <div className="relative min-h-0 bg-slate-50">
        <div className="absolute inset-0 overflow-hidden bg-slate-50">
        {item.imageUrl && failedImageUrl !== item.imageUrl ? (
          <Image
            src={item.imageUrl}
            alt={item.name}
            fill
            sizes="(orientation: portrait) 50vw, 25vw"
            unoptimized
            className={cn("menu-item-image", item.imageFit === "contain" ? "object-contain p-3" : "object-cover")}
            onError={() => setFailedImageUrl(item.imageUrl ?? null)}
          />
        ) : (
          <span
            data-testid="kiosk-product-image-fallback"
            className="grid h-full w-full place-items-center bg-[linear-gradient(145deg,#F8FAFC,#E5E7EB)] text-slate-500"
          >
            <span className="grid h-14 w-14 place-items-center rounded-2xl border border-white/80 bg-white/75 shadow-sm">
              <Package size={28} />
            </span>
          </span>
        )}
        {!simple && item.statusLabel && (
          <span className={cn(
            "absolute max-w-[58%] truncate rounded-full font-black",
            landscape ? "right-2 top-2 px-2 py-0.5 text-[10px]" : "right-3 top-3 px-2.5 py-1 text-[11px]",
            item.disabled ? "bg-slate-900 text-white" : "bg-amber-100 text-amber-800"
          )}>
            {item.statusLabel}
          </span>
        )}
        </div>
        {item.hideActions ? null : Number(item.quantityInCart) > 0 ? (
          <div className={cn("absolute -bottom-3 right-2 z-10 grid shrink-0 overflow-hidden border-2 border-white bg-white shadow-[0_10px_20px_rgba(15,23,42,0.14)]", quantityGridClass)}>
            <motion.button whileTap={{ scale: 0.95 }} type="button" data-guided-test="quantity-minus" onClick={() => onDecrease(item)} className={cn("grid place-items-center bg-slate-50 text-slate-950", quantityCellClass)} aria-label={`Decrease ${item.name}`}><Minus size={17} /></motion.button>
            <span className={cn("grid place-items-center font-black tabular-nums", quantityTextClass)}>{item.quantityInCart}</span>
            <motion.button whileTap={{ scale: 0.95 }} type="button" data-guided-test="quantity-plus" onClick={() => onIncrease(item)} disabled={item.disabled} className={cn("grid place-items-center bg-[var(--kiosk-accent)] text-[var(--kiosk-accent-foreground)] disabled:opacity-50", quantityCellClass)} aria-label={`Increase ${item.name}`}><Plus size={17} /></motion.button>
          </div>
        ) : (
          <motion.button
            whileTap={{ scale: 0.95 }}
            type="button"
            data-guided-test="add-item"
            onClick={() => !item.disabled && onAdd(item)}
            disabled={item.disabled}
            className={cn("absolute -bottom-3 right-2 z-10 grid shrink-0 place-items-center border-2 border-white bg-[var(--kiosk-accent)] text-sm font-black tracking-wide text-[var(--kiosk-accent-foreground)] shadow-[0_10px_20px_var(--kiosk-accent-ring)] transition hover:bg-[var(--kiosk-accent-hover)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--kiosk-accent-ring)] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500", actionButtonClass)}
            aria-label={item.disabled ? item.statusLabel || `${item.name} unavailable` : `Add ${item.name}`}
          >
            ADD
          </motion.button>
        )}
      </div>
      <div className={cn("flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden", contentPaddingClass)}>
        <div className="min-w-0 pr-[34%]">
            {item.showPrice === false ? (
              <p className={cn("truncate font-black leading-none text-slate-500", landscape ? "text-[14px]" : density === "compact" ? "text-[16px]" : "text-xl")}>Ask staff</p>
            ) : (
              <p className="menu-item-price flex min-w-0 items-baseline gap-2 whitespace-nowrap">
                <span className={cn("font-black leading-none", priceClass)}>{item.priceLabel ?? money(item.price, currencySymbol)}</span>
                {!simple && item.originalPrice != null && <span className={cn("truncate font-bold text-slate-400 line-through", landscape ? "text-[10px]" : "text-xs")}>{money(item.originalPrice, currencySymbol)}</span>}
              </p>
            )}
        </div>
        {!simple && item.discount && <p className={cn("mt-1 truncate font-black text-emerald-700", landscape || compactDensity ? "text-[10px]" : "text-xs")}>{item.discount}</p>}
        <h3 className={cn("menu-item-title mt-2 min-h-[2.16em] min-w-0 break-words font-black leading-[1.08]", titleClass)}>{item.name}</h3>
        {!simple && (item.metaLabel || item.secondaryMetaLabel || item.timeLabel || item.dietaryType) && (
          <div className="mt-auto flex min-w-0 items-center gap-2 pt-1.5">
            {item.dietaryType && <span className={cn("grid shrink-0 place-items-center rounded-[4px] border-2", landscape ? "h-4 w-4" : "h-5 w-5", dietaryColor)} title={item.dietaryType}><span className={cn("rounded-full bg-current", landscape ? "h-1.5 w-1.5" : "h-2 w-2")} /></span>}
            <p className={cn("menu-item-meta min-w-0 font-semibold text-slate-500", landscape || compactDensity ? "text-[10px]" : "text-sm")}>{[item.metaLabel, item.secondaryMetaLabel, item.timeLabel].filter(Boolean).join(" · ")}</p>
          </div>
        )}
      </div>
    </motion.article>
  );
}
