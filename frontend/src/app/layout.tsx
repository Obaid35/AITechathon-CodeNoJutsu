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
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased min-h-screen bg-[var(--nk-bg)]">
        {children}
      </body>
    </html>
  );
}
