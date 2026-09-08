function KioskSkeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-[24px] bg-[#E5E7EB] ${className}`} />;
}

export default function KioskLoading() {
  return (
    <main className="min-h-dvh overflow-hidden bg-[#F8FAFC] p-4 text-[#0F172A]">
      <div className="mx-auto flex min-h-[calc(100dvh-2rem)] w-full max-w-5xl flex-col gap-5 rounded-[28px] border border-[#E2E8F0] bg-white p-4 shadow-[0_18px_48px_rgba(15,23,42,0.08)]">
        <div className="flex min-w-0 items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <KioskSkeleton className="h-14 w-14 shrink-0" />
            <div className="min-w-0">
              <KioskSkeleton className="h-5 w-36" />
              <KioskSkeleton className="mt-2 h-4 w-28" />
            </div>
          </div>
          <KioskSkeleton className="h-12 w-24" />
        </div>
        <KioskSkeleton className="h-14 w-full" />
        <KioskSkeleton className="h-48 w-full" />
        <div className="grid min-w-0 grid-cols-2 gap-3 sm:grid-cols-3">
          <KioskSkeleton className="h-44" />
          <KioskSkeleton className="h-44" />
          <KioskSkeleton className="h-44" />
        </div>
        <KioskSkeleton className="mt-auto h-20 w-full" />
      </div>
    </main>
  );
}
