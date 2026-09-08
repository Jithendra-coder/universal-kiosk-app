"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { cn } from "@/lib/utils";

type TypewriterProps = {
  texts: string[];
  className?: string;
  cursorClassName?: string;
  speedMs?: number;
  deleteSpeedMs?: number;
  waitMs?: number;
  cursor?: string;
};

type TypewriterTextProps = Omit<TypewriterProps, "texts"> & {
  texts: string[];
  typewriterKey?: string;
};

export function TypewriterText({ texts, typewriterKey, ...props }: TypewriterTextProps) {
  const phrases = texts.map((text) => text.trim()).filter(Boolean);
  if (phrases.length <= 1) {
    return <span className={props.className}>{phrases[0] ?? ""}</span>;
  }
  return <Typewriter key={typewriterKey ?? phrases.join("|")} texts={phrases} {...props} />;
}

export function Typewriter({
  texts,
  className,
  cursorClassName,
  speedMs = 60,
  deleteSpeedMs = 34,
  waitMs = 1700,
  cursor = "|",
}: TypewriterProps) {
  const shouldReduceMotion = useReducedMotion();
  const phrases = useMemo(() => texts.map((text) => text.trim()).filter(Boolean), [texts]);
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [visibleText, setVisibleText] = useState(phrases[0] ?? "");
  const [deleting, setDeleting] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const phraseKey = phrases.join("\n");

  useEffect(() => {
    if (phrases.length <= 1 || shouldReduceMotion) return undefined;
    const timer = setTimeout(() => {
      setPhraseIndex(0);
      setVisibleText("");
      setDeleting(false);
      setWaiting(false);
    }, 0);
    return () => clearTimeout(timer);
  }, [phraseKey, phrases.length, shouldReduceMotion]);

  useEffect(() => {
    if (phrases.length <= 1 || shouldReduceMotion) {
      return undefined;
    }

    const current = phrases[phraseIndex] ?? phrases[0];
    let timer: ReturnType<typeof setTimeout>;

    if (waiting) {
      timer = setTimeout(() => setWaiting(false), waitMs);
      return () => clearTimeout(timer);
    }

    if (!deleting && visibleText.length < current.length) {
      timer = setTimeout(() => setVisibleText(current.slice(0, visibleText.length + 1)), speedMs);
      return () => clearTimeout(timer);
    }

    if (!deleting && visibleText.length === current.length) {
      timer = setTimeout(() => {
        setDeleting(true);
        setWaiting(false);
      }, waitMs);
      return () => clearTimeout(timer);
    }

    if (deleting && visibleText.length > 0) {
      timer = setTimeout(() => setVisibleText(current.slice(0, visibleText.length - 1)), deleteSpeedMs);
      return () => clearTimeout(timer);
    }

    timer = setTimeout(() => {
      setDeleting(false);
      setWaiting(true);
      setPhraseIndex((index) => (index + 1) % phrases.length);
    }, 140);
    return () => clearTimeout(timer);
  }, [deleteSpeedMs, deleting, phraseIndex, phrases, shouldReduceMotion, speedMs, visibleText, waitMs, waiting]);

  const renderedText = phrases.length <= 1 || shouldReduceMotion ? (phrases[0] ?? "") : visibleText;

  return (
    <span className={cn("inline", className)}>
      {renderedText}
      {phrases.length > 1 && !shouldReduceMotion && (
        <motion.span
          aria-hidden="true"
          className={cn("ml-1 inline-block", cursorClassName)}
          animate={{ opacity: [1, 0.18, 1] }}
          transition={{ duration: 0.9, repeat: Infinity, ease: "easeInOut" }}
        >
          {cursor}
        </motion.span>
      )}
    </span>
  );
}
