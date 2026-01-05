"use client";

import { BarChart2, ChevronDown, Cpu, Globe, Layers, LayoutDashboard, Search, TrendingUp } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ThemeToggle } from "./ThemeToggle";

interface NavDropdownProps {
  label: string;
  items: { label: string; icon: any; href: string }[];
  active?: boolean;
}

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
    <div className="nav-dropdown" ref={dropdownRef}>
      <button className={`nav-link ${active ? "active" : ""} ${isOpen ? "open" : ""}`} onClick={() => setIsOpen(!isOpen)}>
        <span>{label}</span>
        <ChevronDown size={14} className={`chevron ${isOpen ? "rotated" : ""}`} />
      </button>

      {isOpen && (
        <div className="dropdown-menu">
          {items.map((item) => (
            <Link key={item.label} href={item.href} className="dropdown-item" onClick={() => setIsOpen(false)}>
              <item.icon size={16} className="item-icon" />
              <span>{item.label}</span>
            </Link>
          ))}
        </div>
      )}

      <style jsx>{`
        .nav-dropdown {
          position: relative;
          display: flex;
          align-items: center;
        }

        .nav-link {
          background: none;
          border: none;
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 0 12px;
          height: 36px;
          font-size: 14px;
          font-weight: 600;
          color: var(--text-secondary);
          cursor: pointer;
          transition: color 0.2s;
          white-space: nowrap;
        }

        .nav-link:hover,
        .nav-link.open {
          color: var(--text-primary);
        }

        .nav-link.active {
          color: var(--accent-primary);
        }

        .chevron {
          transition: transform 0.2s;
        }

        .chevron.rotated {
          transform: rotate(180deg);
        }

        .dropdown-menu {
          position: absolute;
          top: 100%;
          left: 0;
          min-width: 200px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 8px;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
          z-index: 1000;
          margin-top: 8px;
        }

        .dropdown-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 12px;
          border-radius: 8px;
          color: var(--text-primary);
          text-decoration: none;
          font-size: 14px;
          font-weight: 500;
          transition: background 0.2s;
        }

        .dropdown-item:hover {
          background: var(--bg-tertiary);
        }

        .item-icon {
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}

export function Navbar() {
  const pathname = usePathname();
  const [search, setSearch] = useState("");

  const cryptoItems = [
    { label: "By Market Cap", icon: TrendingUp, href: "/" },
    { label: "Categories", icon: Layers, href: "#" },
  ];

  const exchangeItems = [
    { label: "Spot", icon: Globe, href: "#" },
    { label: "Derivatives", icon: Cpu, href: "#" },
  ];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!search) return;
    const cleanSymbol = search.trim().toUpperCase().replace("/", "-");
    window.location.href = `/chart/${cleanSymbol}-USDT`;
  };

  if (pathname?.startsWith("/chart")) return null;

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="nav-left">
          <Link href="/" className="brand">
            <LayoutDashboard size={24} className="brand-icon" />
            <span className="brand-name">Argus</span>
          </Link>

          <div className="nav-menu">
            <Link href="#" className="nav-static-link">
              <BarChart2 size={16} />
              <span>Analytics</span>
            </Link>
          </div>
        </div>

        <div className="nav-right">
          <form className="search-bar" onSubmit={handleSearch}>
            <Search size={14} className="search-icon" />
            <input type="text" placeholder="Search coin..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </form>
          <div className="divider" />
          <ThemeToggle />
        </div>
      </div>

      <style jsx>{`
        .navbar {
          height: 56px;
          background: var(--bg-primary);
          border-bottom: 1px solid var(--border-color);
          position: sticky;
          top: 0;
          z-index: 1000;
        }

        .navbar-container {
          max-width: 1440px;
          margin: 0 auto;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 20px;
        }

        .nav-left {
          display: flex;
          align-items: center;
          gap: 32px;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 10px;
          text-decoration: none;
        }

        .brand-icon {
          color: var(--accent-primary);
        }

        .brand-name {
          font-size: 20px;
          font-weight: 800;
          color: var(--text-primary);
          letter-spacing: -0.5px;
        }

        .nav-menu {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .nav-static-link {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 0 12px;
          height: 36px;
          font-size: 14px;
          font-weight: 600;
          color: var(--text-secondary);
          text-decoration: none;
          transition: all 0.2s;
          border-radius: 8px;
        }

        .nav-static-link:hover {
          color: var(--text-primary);
          background: var(--bg-tertiary);
        }

        .nav-right {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .search-bar {
          display: flex;
          align-items: center;
          gap: 8px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 0 12px;
          height: 34px;
          width: 200px;
          transition: all 0.2s ease;
        }

        .search-bar:focus-within {
          border-color: var(--accent-primary);
          width: 240px;
          background: var(--bg-secondary);
        }

        .search-icon {
          color: var(--text-muted);
        }

        .search-bar input {
          background: none;
          border: none;
          outline: none;
          color: var(--text-primary);
          font-size: 13px;
          width: 100%;
        }

        .divider {
          width: 1px;
          height: 20px;
          background: var(--border-color);
        }

        @media (max-width: 1024px) {
          .nav-menu {
            display: none;
          }
        }
      `}</style>
    </nav>
  );
}
