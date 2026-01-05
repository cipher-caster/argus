"use client";

import { ChevronLeft, ChevronRight, LayoutDashboard, LineChart, Settings, Star, Wallet } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { cn } from "@/lib/utils";

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", icon: LayoutDashboard, href: "/" },
    { name: "Markets", icon: LineChart, href: "#" },
    { name: "Watchlist", icon: Star, href: "#" },
    { name: "Portfolio", icon: Wallet, href: "#" },
  ];

  const isActive = (href: string) => pathname === href;

  return (
    <aside className={cn("bg-secondary border-r border-border flex flex-col transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shrink-0 z-50 h-screen", collapsed ? "w-16" : "w-60")}>
      <div className="h-[60px] flex items-center justify-between px-4 border-b border-border overflow-hidden whitespace-nowrap">
        {!collapsed && <span className="font-extrabold text-[16px] text-primary">Argus Terminal</span>}
        <button className="bg-muted border border-border rounded w-6 h-6 flex items-center justify-center text-muted-foreground transition-all hover:bg-border hover:text-foreground" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      <nav className="flex-1 p-2 flex flex-col gap-1 overflow-x-hidden">
        {navItems.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center p-2.5 rounded-lg no-underline transition-all duration-200 whitespace-nowrap overflow-hidden group",
              isActive(item.href) ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
            title={collapsed ? item.name : ""}
          >
            <item.icon size={20} className="shrink-0" />
            {!collapsed && <span className="ml-3 text-sm font-medium">{item.name}</span>}
          </Link>
        ))}
      </nav>

      <div className="p-2 border-t border-border">
        <Link href="#" className="flex items-center p-2.5 rounded-lg no-underline text-muted-foreground transition-all hover:bg-muted hover:text-foreground" title={collapsed ? "Settings" : ""}>
          <Settings size={20} className="shrink-0" />
          {!collapsed && <span className="ml-3 text-sm font-medium">Settings</span>}
        </Link>
      </div>
    </aside>
  );
}
