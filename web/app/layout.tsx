import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrintHub - Student Print Service",
  description: "Easy print ordering and tracking for students",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased bg-gray-50">
        {children}
      </body>
    </html>
  );
}
