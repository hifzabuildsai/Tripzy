import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tripzy",
  description: "AI-powered travel planning, built around your journey.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}