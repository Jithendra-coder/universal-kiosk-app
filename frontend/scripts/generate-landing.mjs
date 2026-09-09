import fs from 'node:fs';
import path from 'node:path';

const htmlPath = path.resolve('landing pages demo/01-menutap-scroll-kiosk.html');
if (!fs.existsSync(htmlPath)) {
  console.log('Demo HTML not found; skipping landing generation.');
  process.exit(0);
}
const html = fs.readFileSync(htmlPath, 'utf8');

// 1. Extract CSS
const styleMatch = html.match(/<style>([\s\S]*?)<\/style>/i);
if (!styleMatch) {
  console.error('No style match found');
  process.exit(1);
}
let css = styleMatch[1].replace(/hand-cursor-retina\.png/g, '/hand-cursor-retina.png');
fs.writeFileSync('frontend/src/app/landing.css', css, 'utf8');
console.log('Wrote frontend/src/app/landing.css');

// 2. Extract Body HTML
const bodyMatch = html.match(/<body>([\s\S]*?)<script>/i);
if (!bodyMatch) {
  console.error('No body match found');
  process.exit(1);
}
let body = bodyMatch[1].trim();

// Update image and links in body
body = body.replace(/src="hand-cursor-retina\.png"/g, 'src="/hand-cursor-retina.png"');
body = body.replace(/<a href="#" class="nav-signin">Sign In<\/a>/g, '<a href="/auth/sign-in" class="nav-signin">Sign In</a>');
body = body.replace(/<a href="#" class="btn-primary">([\s\S]*?)Get Started Free([\s\S]*?)<\/a>/g, '<a href="/auth/sign-in" class="btn-primary">$1Get Started Free$2</a>');
body = body.replace(/<a href="#" class="btn-cta-large">([\s\S]*?)Start Your 14 Day Free Trial([\s\S]*?)<\/a>/g, '<a href="/auth/sign-in" class="btn-cta-large">$1Start Your 14 Day Free Trial$2</a>');

// 3. Extract Script Logic into landing-engine.js
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/i);
if (!scriptMatch) {
  console.error('No script match found');
  process.exit(1);
}

let scriptCode = scriptMatch[1].trim();
scriptCode = scriptCode.replace(/^\(function\(\)\s*\{/, '');
scriptCode = scriptCode.replace(/'use strict';/, '');
scriptCode = scriptCode.replace(/\}\)\(\);?\s*$/, '');

scriptCode = scriptCode.replace(/setInterval\(updateKioskTime, 1000\);/g, 'clockIntervalId = setInterval(updateKioskTime, 1000);');
scriptCode = scriptCode.replace(/requestAnimationFrame\(renderFrame\);/g, 'animFrameId = requestAnimationFrame(renderFrame);');

const landingEngineJs = `export function initLandingEngine() {
  let animFrameId;
  let clockIntervalId;

  ${scriptCode}

  return function cleanup() {
    if (animFrameId) cancelAnimationFrame(animFrameId);
    if (clockIntervalId) clearInterval(clockIntervalId);
    window.removeEventListener('scroll', updateScrollProgress);
    window.removeEventListener('resize', updateScrollProgress);
    window.removeEventListener('resize', measureElements);
  };
}
`;

fs.writeFileSync('frontend/src/app/landing-engine.js', landingEngineJs, 'utf8');
console.log('Wrote frontend/src/app/landing-engine.js');

// 4. Create page.tsx
const pageTsx = `"use client";

import React, { useEffect, useState } from "react";
import "./landing.css";
// @ts-ignore
import { initLandingEngine } from "./landing-engine.js";

const LANDING_HTML = ${JSON.stringify(body)};

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const cleanup = initLandingEngine();
    return () => {
      if (typeof cleanup === "function") cleanup();
    };
  }, [mounted]);

  return (
    <div
      id="landing-page-root"
      dangerouslySetInnerHTML={{ __html: LANDING_HTML }}
      suppressHydrationWarning
    />
  );
}
`;

fs.writeFileSync('frontend/src/app/page.tsx', pageTsx, 'utf8');
console.log('Successfully generated frontend/src/app/page.tsx with landing-engine.js');
