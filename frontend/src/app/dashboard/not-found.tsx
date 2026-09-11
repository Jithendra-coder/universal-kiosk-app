import Link from "next/link";
import { PageContainer } from "@/components/layout/DashboardPrimitives";

export default function DashboardNotFound() {
  return (
    <PageContainer width="compact" style={{ padding: "48px 16px" }}>
      <div
        className="mt-feedback-state"
        style={{
          padding: "36px 24px",
          background: "#fff",
          borderRadius: "16px",
          border: "1px solid #e4e7ec",
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "12px",
        }}
      >
        <span
          style={{
            fontSize: "12px",
            fontWeight: 700,
            padding: "4px 10px",
            borderRadius: "999px",
            background: "#eff8ff",
            color: "#175cd3",
          }}
        >
          404 Not Found
        </span>
        <h1 style={{ margin: "4px 0 0", fontSize: "20px", fontWeight: 700, color: "#101828" }}>
          Section not found
        </h1>
        <p style={{ margin: 0, fontSize: "14px", lineHeight: "20px", color: "#667085" }}>
          The requested dashboard view or resource could not be found.
        </p>
        <div style={{ marginTop: "6px" }}>
          <Link href="/dashboard" className="mt-button mt-button--primary">
            Go to Home
          </Link>
        </div>
      </div>
    </PageContainer>
  );
}
