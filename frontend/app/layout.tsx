import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Smart RAG Search — AI Document Assistant",
  description:
    "Production-grade Retrieval-Augmented Generation document search powered by Google Gemini AI, pgvector semantic search, and Redis caching.",
  keywords: ["RAG", "AI", "document search", "Gemini", "pgvector", "semantic search"],
  authors: [{ name: "Smart RAG Search" }],
  openGraph: {
    title: "Smart RAG Search — AI Document Assistant",
    description: "Search your documents intelligently with cited AI answers",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
