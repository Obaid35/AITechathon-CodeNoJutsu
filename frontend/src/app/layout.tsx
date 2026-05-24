import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NaqsKAR — AI Complaint Triage for Pakistan",
  description: "AI-Powered Citizen Complaint Triage & Routing System for Pakistan's public infrastructure",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased min-h-screen bg-[var(--nk-bg)]" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
