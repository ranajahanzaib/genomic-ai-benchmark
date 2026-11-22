import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Genomic AI Benchmark — Research Observatory",
  description: "An independent laboratory for evaluating genomic intelligence.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
