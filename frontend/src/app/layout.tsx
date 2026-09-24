import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tripzy — Give me the trip",
  description: "An AI travel-planning agent that takes your mission from idea to researched itinerary.",
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
