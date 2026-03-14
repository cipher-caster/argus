import { Navbar } from "@/components/common/Navbar";
import { Providers } from "@/components/common/Providers";
import { ToastProvider } from "@/components/ui/toaster";
import type { Metadata } from "next";
import { DM_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});

const dmMono = DM_Mono({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Argus",
  description: "AI-Enhanced Crypto Trading Dashboard",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 36 36'><rect width='36' height='36' rx='9' fill='%236366f1'/><path d='M4 18 C8 10 28 10 32 18 C28 26 8 26 4 18Z' fill='rgba(255,255,255,0.08)' stroke='rgba(255,255,255,0.9)' stroke-width='1.2'/><circle cx='18' cy='18' r='6' fill='rgba(255,255,255,0.12)' stroke='rgba(255,255,255,0.5)' stroke-width='1'/><circle cx='18' cy='18' r='3.5' fill='rgba(255,255,255,0.2)' stroke='rgba(255,255,255,0.7)' stroke-width='1'/><circle cx='18' cy='18' r='2' fill='white'/><circle cx='19.8' cy='16.2' r='0.8' fill='rgba(255,255,255,0.6)'/></svg>",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" className={`${spaceGrotesk.variable} ${dmMono.variable}`}>
      <body>
        <Providers>
          <div className="layout-main h-full flex flex-col">
            <Navbar />
            <div className="content-scrollable flex-1 min-h-0 relative overflow-y-auto">
              <ToastProvider>
                {children}
              </ToastProvider>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
