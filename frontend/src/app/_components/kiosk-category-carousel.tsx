"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { ChevronLeft, ChevronRight, LayoutGrid } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { BusinessType } from "@/lib/types";
import { type KioskCategoryStyle } from "@/lib/kiosk/kiosk-business-config";

export type KioskCategoryCarouselItem = {
  id: string | number;
  name: string;
  imageUrl?: string;
  itemCount?: number;
};

export type KioskCategoryCarouselProps = {
  categories: KioskCategoryCarouselItem[];
  activeCategoryId: string | number;
  onCategoryChange: (categoryId: string | number) => void;
  businessType: BusinessType;
  categoryStyle?: KioskCategoryStyle;
  className?: string;
  centered?: boolean;
  density?: "normal" | "compact";
};

function CategoryThumbnail({ imageUrl }: { imageUrl?: string }) {
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);

  if (!imageUrl || failedImageUrl === imageUrl) {
    return (
      <span
        data-testid="kiosk-category-image-fallback"
        className="grid h-full w-full place-items-center bg-[linear-gradient(145deg,#F8FAFC,#E5E7EB)] text-slate-500"
      >
        <LayoutGrid size={28} />
      </span>
    );
  }

  return <Image src={imageUrl} alt="" fill sizes="168px" unoptimized className="object-cover" onError={() => setFailedImageUrl(imageUrl)} />;
}

export function KioskCategoryCarousel({
  categories,
  activeCategoryId,
  onCategoryChange,
  businessType,
  categoryStyle = "image_cards",
  className,
  centered = false,
  density = "normal",
}: KioskCategoryCarouselProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [canLeft, setCanLeft] = useState(false);
  const [canRight, setCanRight] = useState(false);
  void businessType;

  const updateArrows = () => {
    const element = viewportRef.current;
    if (!element) return;
    setCanLeft(element.scrollLeft > 8);
    setCanRight(element.scrollLeft + element.clientWidth < element.scrollWidth - 8);
  };

  useEffect(() => {
    updateArrows();
    const element = viewportRef.current;
    if (!element) return;
    const observer = new ResizeObserver(updateArrows);
    observer.observe(element);
    return () => observer.disconnect();
  }, [categories.length]);

  const scroll = (direction: number) => {
    viewportRef.current?.scrollBy({ left: direction * Math.max(280, viewportRef.current.clientWidth * 0.72), behavior: "smooth" });
  };
  const simple = categoryStyle === "simple_button" || categoryStyle === "motion_tabs";

  return (
    <div data-testid="kiosk-category-carousel" className={cn("relative min-w-0", className)}>
      {canLeft && (
        <button
          type="button"
          onClick={() => scroll(-1)}
          className="absolute left-1 top-1/2 z-10 grid h-12 w-12 -translate-y-1/2 place-items-center rounded-full border border-slate-200 bg-white text-slate-900 shadow-lg"
          aria-label="Previous categories"
        >
          <ChevronLeft size={24} />
        </button>
      )}
      <div
        ref={viewportRef}
        onScroll={updateArrows}
        className={cn(
          density === "compact"
            ? "flex min-w-0 snap-x snap-mandatory gap-3 overflow-x-auto overflow-y-hidden px-1 py-1.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            : "flex min-w-0 snap-x snap-mandatory gap-6 overflow-x-auto overflow-y-hidden px-2 py-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
          centered && "justify-center"
        )}
      >
        {categories.map((category, index) => {
          const active = String(category.id) === String(activeCategoryId);
          if (simple) {
            return (
              <motion.button
                key={category.id}
                type="button"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: active ? -2 : 0, scale: active ? 1.02 : 1 }}
                transition={{ duration: 0.22, delay: Math.min(index * 0.02, 0.16) }}
                whileTap={{ scale: 0.97 }}
                onClick={() => onCategoryChange(category.id)}
                className={cn(
                  density === "compact"
                    ? "relative flex h-[clamp(44px,7vh,64px)] min-w-[clamp(88px,10vw,118px)] shrink-0 snap-start items-center justify-center rounded-xl border px-3 text-center transition"
                    : "relative flex h-[clamp(58px,9vh,86px)] min-w-[clamp(118px,15vw,168px)] shrink-0 snap-start items-center justify-center rounded-2xl border px-5 text-center transition",
                  active
                    ? "border-[var(--kiosk-accent)] bg-[var(--kiosk-accent-soft)] text-slate-950 shadow-[0_10px_24px_var(--kiosk-accent-ring)]"
                    : "border-slate-200 bg-white text-slate-700 shadow-sm"
                )}
              >
                <span className={cn("line-clamp-2 break-words font-black leading-tight", density === "compact" ? "text-[clamp(12px,1.05vw,16px)]" : "text-[clamp(17px,1.8vw,26px)]")}>{category.name}</span>
                {active && <span className="absolute inset-x-5 bottom-0 h-1 rounded-t-full bg-[var(--kiosk-accent)]" />}
              </motion.button>
            );
          }
          return (
            <motion.button
              key={category.id}
              type="button"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: active ? -3 : 0, scale: active ? 1.025 : 1 }}
              transition={{ duration: 0.24, delay: Math.min(index * 0.025, 0.18) }}
              whileTap={{ scale: 0.96 }}
              onClick={() => onCategoryChange(category.id)}
              className={cn(
                density === "compact"
                  ? "relative h-[clamp(58px,9vh,88px)] w-[clamp(88px,10vw,118px)] shrink-0 snap-start overflow-hidden rounded-xl border bg-white text-white transition"
                  : "relative h-[clamp(72px,12vh,132px)] w-[clamp(124px,16vw,168px)] shrink-0 snap-start overflow-hidden rounded-2xl border bg-white text-white transition",
                active
                  ? "border-[var(--kiosk-accent)] shadow-[0_14px_30px_var(--kiosk-accent-ring)] ring-2 ring-[var(--kiosk-accent-ring)]"
                  : "border-slate-200 shadow-sm"
              )}
            >
              <span className="absolute inset-0 grid place-items-center overflow-hidden bg-slate-50">
                <CategoryThumbnail imageUrl={category.imageUrl} />
              </span>
              <span className={cn("absolute inset-x-0 bottom-0 min-w-0 bg-gradient-to-t from-slate-950/92 via-slate-950/58 to-transparent text-center", density === "compact" ? "px-2 pb-2 pt-7" : "px-3 pb-3 pt-10")}>
                <span className={cn("line-clamp-2 break-words font-black leading-[1.04] text-white", density === "compact" ? "text-[clamp(12px,1.05vw,16px)]" : "text-[clamp(17px,2vw,27px)]")}>{category.name}</span>
              </span>
              {active && <span className="absolute inset-x-3 bottom-0 h-1 rounded-t-full bg-[var(--kiosk-accent)]" />}
            </motion.button>
          );
        })}
      </div>
      {canRight && (
        <button
          type="button"
          onClick={() => scroll(1)}
          className="absolute right-1 top-1/2 z-10 grid h-12 w-12 -translate-y-1/2 place-items-center rounded-full border border-slate-200 bg-white text-slate-900 shadow-lg"
          aria-label="Next categories"
        >
          <ChevronRight size={24} />
        </button>
      )}
    </div>
  );
}
