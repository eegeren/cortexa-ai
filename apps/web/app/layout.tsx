// web/app/layout.tsx
import type { Metadata } from "next";
import Header from "../components/Header";

export const metadata: Metadata = {
  title: "Cortexa",
  description: "Personal AI Copilot",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body style={{ margin: 0, background: "#f3f4f6", color: "#111827", fontFamily: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial' }}>
        <main style={{ maxWidth: 960, margin: "24px auto", padding: "0 16px" }}>
          <Header />
          {children}
        </main>
      </body>
    </html>
  );
}