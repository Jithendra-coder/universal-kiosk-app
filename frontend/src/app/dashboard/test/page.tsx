"use client";

import { useCallback, useEffect, useState } from "react";
import { useBusiness } from "@/components/layout/BusinessProvider";
import { api } from "@/lib/api";
import { formatDateTime, formatDuration } from "@/lib/formatters";

type Session = { id: string; expires_at: string; token?: string };
type Activity = { id: string; label: string; created_at?: string };

export default function TestHubPage() {
  const { business } = useBusiness();
  const [session, setSession] = useState<Session | null>(null);
  const [remaining, setRemaining] = useState(0);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [activity, setActivity] = useState<Activity[]>([]);

  const load = useCallback(async () => {
    if (!business) return;
    setLoading(true);
    try {
      const current = (await api.currentKioskTestSession(business.id)).session;
      setSession(current);
      if (current) {
        const [orders, history] = await Promise.allSettled([api.testKitchenOrders(), api.testKitchenCompleted()]);
        const rows = [
          ...(orders.status === "fulfilled" ? orders.value.orders : []),
          ...(history.status === "fulfilled" ? history.value.orders : []),
        ].flatMap((order) => (Array.isArray(order.lifecycle_events) ? order.lifecycle_events : []).map((event) => {
          const entry = event as Record<string, unknown>;
          return {
          id: String(entry.id),
          created_at: typeof entry.created_at === "string" ? entry.created_at : undefined,
          label: String(entry.event_type || "Test activity").replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase()),
          };
        }));
        setActivity(Array.from(new Map(rows.map((row) => [row.id, row])).values()).sort((a, b) => String(b.created_at).localeCompare(String(a.created_at))).slice(0, 10));
      } else setActivity([]);
      setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load the test workspace."); }
    finally { setLoading(false); }
  }, [business]);

  useEffect(() => { void Promise.resolve().then(load); }, [load]);
  useEffect(() => {
    const tick = () => setRemaining(session ? Math.max(0, new Date(session.expires_at).getTime() - Date.now()) : 0);
    const initial = window.setTimeout(tick, 0); const timer = window.setInterval(tick, 1000); return () => { window.clearTimeout(initial); window.clearInterval(timer); };
  }, [session]);

  const start = async (reset = false) => {
    if (!business) return;
    setWorking(true);
    try {
      const response = reset ? await api.resetKioskTestSession(business.id) : await api.createKioskTestSession(business.id);
      await api.exchangeKioskTestSession(response.session.token || "");
      setSession(response.session); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not start the isolated test workspace."); }
    finally { setWorking(false); }
  };

  const end = async () => {
    if (!business) return;
    setWorking(true);
    try { await api.endKioskTestSession(business.id); await api.clearKioskTestSession().catch(() => undefined); setSession(null); setRemaining(0); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not end the test workspace."); }
    finally { setWorking(false); }
  };

  const resetData = async () => {
    if (!window.confirm("Reset test data? This clears only the current isolated test session.")) return;
    setWorking(true);
    try { await api.testRuntimeReset(); setActivity([]); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not reset isolated test data."); }
    finally { setWorking(false); }
  };

  return <section className="mt-page mt-page--dashboard mt-test-device-page" aria-labelledby="test-hub-title">
    <div className="mt-page-header"><div><p className="mt-eyebrow">Isolated workspace</p><h1 id="test-hub-title">Test Device</h1><p className="mt-page-subtitle">Test Kiosk, Counter, and Kitchen together in an isolated environment without affecting live operations.</p></div></div>
    {error && <div className="mt-state mt-state--error" role="alert"><strong>Test workspace unavailable</strong><span>{error}</span><button type="button" className="mt-button mt-button--secondary" onClick={() => void load()}>Try again</button></div>}
    <div className="mt-card mt-test-session-card"><div className="mt-card-header"><div><h2>Isolated Test Session</h2><p className="mt-type-card-description">Server-controlled access. Test orders and payments never reach live operations.</p></div><span className={`mt-status-pill ${session && remaining ? "mt-status-pill--success" : "mt-status-pill--muted"}`}>{session && remaining ? "Active" : "Not running"}</span></div>{loading ? <p role="status">Loading test session…</p> : session && remaining ? <div className="mt-test-hub-session"><strong>{formatDuration(Math.ceil(remaining / 1000))} remaining</strong><span>Expires {formatDateTime(session.expires_at, business?.timezone || undefined)}</span><div className="mt-button-row"><button type="button" className="mt-button mt-button--secondary" onClick={() => void resetData()} disabled={working}>Reset test data</button><button type="button" className="mt-button mt-button--secondary" onClick={() => void start(true)} disabled={working}>Reset session</button><button type="button" className="mt-button mt-button--secondary" onClick={() => void end()} disabled={working}>End session</button></div></div> : <button type="button" className="mt-button mt-button--primary" onClick={() => void start()} disabled={working}>{working ? "Starting…" : "Start Test Session"}</button>}</div>
    {session && remaining ? <div className="mt-test-hub-verification">{["Isolated Orders", "Simulated Payments", "No Live Devices", "No Production Writes"].map((label) => <span key={label}>✓ {label}</span>)}</div> : null}
    <section className="mt-test-hub-section"><div className="mt-test-hub-section-header"><div><h2>Test Applications</h2><p className="mt-type-card-description">Open each application in a separate tab and test the connected order flow.</p></div></div><div className="mt-test-hub-apps">{[ ["Test Kiosk", "Place customer orders using the isolated test menu and session.", "/test/kiosk"], ["Test Counter", "Create Counter orders, simulate payments, monitor Kitchen progress, and test handover.", "/test/counter"], ["Test Kitchen", "Receive isolated orders and test preparation, hold, Ready, recall, and rework.", "/test/kitchen"] ].map(([title, description, href]) => <article className="mt-test-hub-app" key={title}><span className="mt-test-hub-app-icon" aria-hidden="true">{title === "Test Kiosk" ? "⌁" : title === "Test Counter" ? "＋" : "✓"}</span><h3>{title}</h3><p>{description}</p>{session && remaining ? <a className="mt-button mt-button--secondary" href={href} target="_blank" rel="noopener noreferrer">Open {title} ↗</a> : <span className="mt-test-hub-disabled">Start session to open</span>}</article>)}</div></section>
    <section className="mt-test-hub-section"><div className="mt-test-hub-section-header"><div><h2>Test Scenarios</h2><p className="mt-type-card-description">Guided workflows for the connected isolated apps.</p></div></div><div className="mt-test-hub-flows"><article><b>Kiosk → Counter → Kitchen</b><span>Place a Pay-at-Counter order, simulate payment, prepare it, and complete handover.</span><small>Kiosk → Payment → Kitchen → Handover</small></article><article><b>Counter Direct Order</b><span>Create and send a direct Counter order through the full lifecycle.</span><small>Counter → Kitchen → Ready → Handover</small></article><article><b>Kitchen Exception Flow</b><span>Exercise operational exceptions without touching production state.</span><small>Preparing → Hold/Resume → Recall/Rework → Ready</small></article></div></section>
    <section className="mt-test-hub-section mt-test-activity"><div className="mt-test-hub-section-header"><div><h2>Test Activity</h2><p className="mt-type-card-description">Recent lifecycle events from the current isolated session.</p></div></div><div className="mt-test-activity-list">{activity.length ? activity.map((event) => <div key={event.id}><span>✓</span><b>{event.label}</b><small>{event.created_at ? formatDateTime(event.created_at, business?.timezone || undefined) : "Just now"}</small></div>) : <p className="mt-type-card-description">No test activity yet. Open an application and start a workflow to see it here.</p>}</div></section>
  </section>;
}
