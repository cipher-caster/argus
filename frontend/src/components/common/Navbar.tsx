"use client";

import { ArgusLogo } from "@/components/common/ArgusLogo";
import { useProviderInfo, useSetProvider } from "@/hooks/useMarketData";
import { BarChart2, ChevronDown, Globe, LineChart, Search, TrendingUp } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ThemeToggle } from "./ThemeToggle";

interface NavDropdownProps {
  label: string;
  items: { label: string; icon: React.ElementType; href: string }[];
  active?: boolean;
}

import { cn } from "@/lib/utils";

function NavDropdown({ label, items, active }: NavDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative flex items-center" ref={dropdownRef}>
      <button
        className={cn("flex items-center gap-1 px-3 h-9 text-sm font-semibold transition-colors whitespace-nowrap", active ? "text-primary" : "text-muted-foreground hover:text-foreground", isOpen && "text-foreground")}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>{label}</span>
        <ChevronDown size={14} className={cn("transition-transform duration-200", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 min-w-[200px] bg-secondary border border-border rounded-xl p-2 shadow-2xl z-[1000] mt-2 animate-in fade-in zoom-in duration-200">
          {items.map((item) => (
            <Link key={item.label} href={item.href} className="flex items-center gap-3 p-2.5 rounded-lg text-foreground no-underline text-sm font-medium transition-colors hover:bg-muted" onClick={() => setIsOpen(false)}>
              <item.icon size={16} className="text-muted-foreground" />
              <span>{item.label}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

const PROVIDERS = ["binance", "okx"] as const;

export function Navbar() {
  const pathname = usePathname();
  const [search, setSearch] = useState("");
  const { data: providerInfo } = useProviderInfo();
  const provider = providerInfo?.provider || null;
  const setProviderMutation = useSetProvider();
  
  const [providerOpen, setProviderOpen] = useState(false);
  const providerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (providerRef.current && !providerRef.current.contains(e.target as Node)) {
        setProviderOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleProviderSwitch(name: string) {
    if (name === provider || setProviderMutation.isPending) return;
    setProviderOpen(false);
    setProviderMutation.mutate(name);
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!search) return;
    const cleanSymbol = search.trim().toUpperCase().replace("/", "-");
    window.location.href = `/chart/${cleanSymbol}-USDT`;
  };

  const isFullWidthPage = pathname?.startsWith("/chart") || pathname === "/analytics" || pathname?.startsWith("/markets") || pathname === "/trading";

  return (
    <nav className="h-14 bg-background border-b border-border sticky top-0 z-[1000]">
      <div className={cn("h-full flex items-center justify-between px-5", !isFullWidthPage && "max-w-[1440px] mx-auto")}>
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5 no-underline">
            <ArgusLogo size={30} />
            <span className="text-xl font-extrabold text-foreground tracking-tighter">Argus</span>
          </Link>

          <div className="hidden lg:flex items-center gap-1">
            <Link
              href="/chart/BTC-USDT"
              className={cn(
                "flex items-center gap-1.5 px-3 h-9 text-sm font-semibold no-underline rounded-lg transition-all",
                pathname?.startsWith("/chart") ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-foreground hover:bg-muted",
              )}
            >
              <LineChart size={16} />
              <span>Charts</span>
            </Link>
            <Link
              href="/markets"
              className={cn("flex items-center gap-1.5 px-3 h-9 text-sm font-semibold no-underline rounded-lg transition-all", pathname === "/markets" ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-foreground hover:bg-muted")}
            >
              <Globe size={16} />
              <span>Markets</span>
            </Link>
            <Link
              href="/analytics"
              className={cn("flex items-center gap-1.5 px-3 h-9 text-sm font-semibold no-underline rounded-lg transition-all", pathname === "/analytics" ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-foreground hover:bg-muted")}
            >
              <BarChart2 size={16} />
              <span>Analytics</span>
            </Link>
            <Link
              href="/trading"
              className={cn("flex items-center gap-1.5 px-3 h-9 text-sm font-semibold no-underline rounded-lg transition-all", pathname === "/trading" ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-foreground hover:bg-muted")}
            >
              <TrendingUp size={16} />
              <span>Trading</span>
            </Link>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <form className="flex items-center gap-2 bg-muted border border-border rounded-lg px-3 h-[34px] w-48 transition-all duration-200 focus-within:w-60 focus-within:border-primary focus-within:bg-background" onSubmit={handleSearch}>
            <Search size={14} className="text-muted-foreground" />
            <input type="text" placeholder="Search coin..." className="bg-transparent border-none outline-none text-foreground text-[13px] w-full placeholder:text-muted-foreground/50" value={search} onChange={(e) => setSearch(e.target.value)} />
          </form>
          {provider && (
            <div className="relative" ref={providerRef}>
              <button
                onClick={() => setProviderOpen((o) => !o)}
                disabled={setProviderMutation.isPending}
                className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md bg-muted text-muted-foreground border border-border hover:border-primary hover:text-foreground transition-colors disabled:opacity-50"
              >
                {setProviderMutation.isPending ? "..." : provider}
                <ChevronDown size={10} className={cn("transition-transform duration-150", providerOpen && "rotate-180")} />
              </button>
              {providerOpen && (
                <div className="absolute right-0 top-full mt-1.5 bg-secondary border border-border rounded-xl p-1 shadow-2xl z-[1001] min-w-[100px] animate-in fade-in zoom-in duration-150">
                  {PROVIDERS.map((name) => (
                    <button
                      key={name}
                      onClick={() => handleProviderSwitch(name)}
                      className={cn(
                        "w-full text-left px-3 py-1.5 rounded-lg text-[11px] font-semibold uppercase tracking-wider transition-colors",
                        name === provider
                          ? "bg-primary/10 text-primary"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground"
                      )}
                    >
                      {name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          <div className="w-px h-5 bg-border" />
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
