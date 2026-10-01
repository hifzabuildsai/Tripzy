import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://tripzy-liard.vercel.app"),
  title: "Tripzy — Give me the trip",
  description:
    "An agentic travel planner that turns a natural-language mission into researched options and a structured, persisted itinerary.",
  applicationName: "Tripzy",
  openGraph: {
    title: "Tripzy — Give me the trip",
    description:
      "From one travel mission to researched options, a structured itinerary, and a durable trip workspace.",
    url: "/",
    siteName: "Tripzy",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Tripzy — Give me the trip",
    description:
      "An agentic travel planner with deterministic state, selective replanning, and durable trip workspaces.",
  },
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
