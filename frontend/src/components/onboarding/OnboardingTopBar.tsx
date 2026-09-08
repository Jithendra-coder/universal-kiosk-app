"use client";

const steps = ["Business Type", "Business Details", "Menu Items", "Kiosk Layout", "Welcome Screen", "Test Kiosk"];

export function MenuTapLogo() {
  return (
    <div className="mt-onboarding-logo" role="img" aria-label="MenuTap">
      <svg className="mt-onboarding-logo__mark" viewBox="0 0 64 52" fill="none" aria-hidden="true">
        <rect x="3" y="3" width="58" height="34" rx="1.5" fill="#fff" stroke="#111827" strokeWidth="3.5" />
        <circle cx="22" cy="17" r="3.2" fill="#a8e000" />
        <circle cx="42" cy="17" r="3.2" fill="#a8e000" />
        <path d="M18 25Q32 34 46 25" stroke="#a8e000" strokeWidth="3" strokeLinecap="round" />
        <path d="M32 37v5m0 0-9 7m9-7 9 7M22 49h20" stroke="#111827" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="mt-onboarding-logo__wordmark"><span>Menu</span><span>Tap</span></span>
    </div>
  );
}

export function OnboardingTopBar({
  currentStep,
  onContinue,
  disabled,
  busy = false,
}: {
  currentStep: number;
  onContinue: () => void;
  disabled: boolean;
  busy?: boolean;
}) {
  return (
    <header className="mt-onboarding-topbar">
      <div className="mt-onboarding-topbar__inner">
        <div className="mt-onboarding-progress" aria-hidden="true">
          {steps.map((_, index) => {
            const step = index + 1;
            if (step < currentStep) {
              return (
                <svg key={step} className="mt-onboarding-progress__tick" viewBox="0 0 14 14" fill="none">
                  <path d="M1 7l4 4 8-9" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              );
            }
            return <span key={step} className={step === currentStep ? "mt-onboarding-progress__current" : "mt-onboarding-progress__future"} />;
          })}
        </div>
        <span className="mt-sr-only">Step {currentStep} of 6: {steps[currentStep - 1]}</span>
        <div className="mt-onboarding-topbar__logo"><MenuTapLogo /></div>
        <button
          type="button"
          className="mt-onboarding-topbar__continue"
          onClick={onContinue}
          disabled={disabled || busy}
          aria-busy={busy}
          aria-label="Continue"
        >
          <span>Continue</span>
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </header>
  );
}
