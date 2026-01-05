import { Navbar } from "@/components/Navbar";
import { Providers } from "@/components/Providers";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Argus",
  description: "AI-Enhanced Crypto Trading Dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <Providers>
          <div className="layout-main">
            <Navbar />
            <div className="content-scrollable">{children}</div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
