"use client";

import Link from "next/link";
import { useState } from "react";
import { AuthField, AuthInput, AuthPrimaryButton, AuthShell, AuthStatus } from "@/components/AuthShell";

export default function PhoneSignUpPage() {
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  return (
    <AuthShell title="Create your account" description="Start by verifying your phone number">
      <AuthStatus tone="info">{message}</AuthStatus>
      <form className="mt-auth-form" onSubmit={(event) => { event.preventDefault(); if (phone.trim()) setMessage("Phone account creation is not configured for this workspace."); }}>
        <AuthField id="phone" label="Phone Number"><AuthInput id="phone" type="tel" placeholder="Enter your phone number" value={phone} onChange={(event) => setPhone(event.target.value)} autoComplete="tel" required /></AuthField>
        <div className="mt-auth-action"><AuthPrimaryButton type="submit" disabled={!phone.trim()}>Verify Phone</AuthPrimaryButton></div>
      </form>
      <div className="mt-auth-route-links"><Link href="/auth/sign-up">Use email instead</Link><Link href="/auth/sign-in">Back to sign in</Link></div>
    </AuthShell>
  );
}
