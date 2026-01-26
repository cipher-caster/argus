import { Navbar } from "@/components/common/Navbar";
import { Providers } from "@/components/common/Providers";
import { ToastProvider } from "@/components/ui/toaster"; // Added import for ToastProvider
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Argus",
  description: "AI-Enhanced Crypto Trading Dashboard",
  icons: {
    icon: "/data/coins/images/argus_logo.png",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <Providers>
          <div className="layout-main h-full flex flex-col">
            <Navbar />
            <div className="content-scrollable flex-1 min-h-0 relative overflow-y-auto">
              <ToastProvider>
                {" "}
                {/* Wrapped children with ToastProvider */}
                {children}
              </ToastProvider>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
