"use client";

import { useEffect, useRef } from "react";

type ParticleKind = "tiny" | "medium" | "large" | "glow";
type Particle = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  glow: number;
  opacity: number;
  color: { r: number; g: number; b: number };
  kind: ParticleKind;
  phase: number;
};

const palette = [
  { r: 0, g: 0, b: 0 },
  { r: 104, g: 114, b: 128 },
  { r: 161, g: 161, b: 170 },
  { r: 75, g: 85, b: 99 },
  { r: 24, g: 24, b: 27 },
];

function seededRandom(a: number, b: number, c: number, d: number) {
  return () => {
    a >>>= 0; b >>>= 0; c >>>= 0; d >>>= 0;
    let value = (a + b) | 0;
    a = b ^ (b >>> 9);
    b = (c + (c << 3)) | 0;
    c = (c << 21) | (c >>> 11);
    d = (d + 1) | 0;
    value = (value + d) | 0;
    c = (c + value) | 0;
    return (value >>> 0) / 4294967296;
  };
}

export function AmbientBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;

    let width = 0;
    let height = 0;
    let frame = 0;
    let particles: Particle[] = [];
    let reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let visible = document.visibilityState === "visible";

    const makeParticles = () => {
      const random = seededRandom(1337, 42, 999, 12345);
      const density = width < 640
        ? { tiny: 16, medium: 8, large: 4, glow: 4 }
        : width < 1024
          ? { tiny: 24, medium: 12, large: 6, glow: 6 }
          : { tiny: 32, medium: 16, large: 8, glow: 8 };
      const motionScale = reducedMotion ? 0.45 : 1;

      const create = (kind: ParticleKind): Particle => {
        let x = 0;
        let y = 0;
        for (let attempt = 0; attempt < 5; attempt += 1) {
          x = random() * width;
          y = random() * height;
          const centered = Math.abs(x - width / 2) < 325 && Math.abs(y - height / 2) < 325;
          if (!centered || random() < 0.18) break;
        }

        const angle = random() * Math.PI * 2;
        let radius = 0;
        let glow = 0;
        let opacity = 0;
        let speed = 0;
        if (kind === "tiny") {
          radius = 0.8 + random();
          opacity = 0.18 + random() * 0.24;
          speed = 0.015 + random() * 0.02;
        } else if (kind === "medium") {
          radius = 2 + random() * 1.5;
          opacity = 0.32 + random() * 0.3;
          speed = 0.01 + random() * 0.016;
        } else if (kind === "large") {
          radius = 4 + random() * 2;
          opacity = 0.55 + random() * 0.27;
          speed = 0.006 + random() * 0.012;
        } else {
          radius = 3 + random() * 2;
          glow = 8 + random() * 6;
          opacity = 0.3 + random() * 0.3;
          speed = 0.004 + random() * 0.01;
        }
        return {
          x,
          y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          radius,
          glow,
          opacity,
          color: palette[Math.floor(random() * palette.length)],
          kind,
          phase: random() * Math.PI * 2,
        };
      };

      particles = (Object.keys(density) as ParticleKind[]).flatMap((kind) =>
        Array.from({ length: Math.floor(density[kind] * motionScale) }, () => create(kind))
      );
    };

    const draw = (time: number) => {
      context.clearRect(0, 0, width, height);

      if (!reducedMotion) {
        const connectable = particles.filter(({ kind }) => kind === "medium" || kind === "large");
        let clusters = 0;
        let segments = 0;
        for (let left = 0; left < connectable.length && clusters < 6 && segments < 14; left += 1) {
          let links = 0;
          for (let right = left + 1; right < connectable.length && links < 2 && segments < 14; right += 1) {
            const first = connectable[left];
            const second = connectable[right];
            const distance = Math.hypot(first.x - second.x, first.y - second.y);
            if (distance >= 145) continue;
            const alpha = (1 - distance / 145) * 0.045;
            context.beginPath();
            context.moveTo(first.x, first.y);
            context.lineTo(second.x, second.y);
            context.strokeStyle = `rgb(104 114 128 / ${alpha})`;
            context.lineWidth = 0.6;
            context.stroke();
            links += 1;
            segments += 1;
          }
          if (links) clusters += 1;
        }
      }

      for (const particle of particles) {
        const opacity = Math.max(0, Math.min(1, particle.opacity + (reducedMotion ? 0 : Math.sin(time * 0.0005 + particle.phase) * 0.08)));
        context.beginPath();
        if (particle.kind === "glow") {
          const gradient = context.createRadialGradient(particle.x, particle.y, 0, particle.x, particle.y, particle.glow);
          gradient.addColorStop(0, `rgb(${particle.color.r} ${particle.color.g} ${particle.color.b} / ${opacity})`);
          gradient.addColorStop(1, `rgb(${particle.color.r} ${particle.color.g} ${particle.color.b} / 0)`);
          context.arc(particle.x, particle.y, particle.glow, 0, Math.PI * 2);
          context.fillStyle = gradient;
        } else {
          context.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
          context.fillStyle = `rgb(${particle.color.r} ${particle.color.g} ${particle.color.b} / ${opacity})`;
        }
        context.fill();

        if (!reducedMotion) {
          particle.x += particle.vx * 16;
          particle.y += particle.vy * 16;
          if (particle.x < -20) particle.x = width + 20;
          if (particle.x > width + 20) particle.x = -20;
          if (particle.y < -20) particle.y = height + 20;
          if (particle.y > height + 20) particle.y = -20;
        }
      }
    };

    const animate = (time: number) => {
      if (visible && !reducedMotion) draw(time);
      if (!reducedMotion) frame = requestAnimationFrame(animate);
    };

    const resize = () => {
      width = innerWidth;
      height = innerHeight;
      const ratio = Math.min(devicePixelRatio || 1, 2);
      canvas.width = width * ratio;
      canvas.height = height * ratio;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      makeParticles();
      if (reducedMotion) draw(0);
    };

    const onVisibilityChange = () => { visible = document.visibilityState === "visible"; };
    const motionQuery = matchMedia("(prefers-reduced-motion: reduce)");
    const onMotionChange = (event: MediaQueryListEvent) => {
      reducedMotion = event.matches;
      cancelAnimationFrame(frame);
      makeParticles();
      if (reducedMotion) draw(0);
      else frame = requestAnimationFrame(animate);
    };

    resize();
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(document.body);
    document.addEventListener("visibilitychange", onVisibilityChange);
    motionQuery.addEventListener("change", onMotionChange);
    if (!reducedMotion) frame = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      document.removeEventListener("visibilitychange", onVisibilityChange);
      motionQuery.removeEventListener("change", onMotionChange);
    };
  }, []);

  return (
    <div className="mt-ambient mt-bg-dots" data-component="noir-ambient-background" aria-hidden="true">
      <canvas ref={canvasRef} className="mt-ambient__canvas" />
      <div className="mt-ambient__atmosphere" />
    </div>
  );
}
