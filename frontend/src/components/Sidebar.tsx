"use client";

import { ChevronLeft, ChevronRight, LayoutDashboard, LineChart, Settings, Star, Wallet } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

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
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        {!collapsed && <span className="logo-text">Argus Terminal</span>}
        <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <Link key={item.name} href={item.href} className={`nav-item ${isActive(item.href) ? "active" : ""}`} title={collapsed ? item.name : ""}>
            <item.icon size={20} className="nav-icon" />
            {!collapsed && <span className="nav-label">{item.name}</span>}
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        <Link href="#" className="nav-item" title={collapsed ? "Settings" : ""}>
          <Settings size={20} className="nav-icon" />
          {!collapsed && <span className="nav-label">Settings</span>}
        </Link>
      </div>

      <style jsx>{`
        .sidebar {
          width: 240px;
          height: 100vh;
          background: var(--bg-secondary);
          border-right: 1px solid var(--border-color);
          display: flex;
          flex-direction: column;
          transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          flex-shrink: 0;
          z-index: 100;
        }

        .sidebar.collapsed {
          width: 64px;
        }

        .sidebar-header {
          height: 60px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 16px;
          border-bottom: 1px solid var(--border-color);
        }

        .logo-text {
          font-weight: 800;
          font-size: 16px;
          color: var(--accent-primary);
          white-space: nowrap;
          overflow: hidden;
        }

        .collapse-btn {
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 4px;
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.2s;
        }

        .collapse-btn:hover {
          background: var(--border-color);
          color: var(--text-primary);
        }

        .sidebar-nav {
          flex: 1;
          padding: 16px 8px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .nav-item {
          display: flex;
          align-items: center;
          padding: 10px 12px;
          border-radius: 8px;
          color: var(--text-secondary);
          text-decoration: none;
          transition: all 0.2s;
          white-space: nowrap;
        }

        .nav-item:hover {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        .nav-item.active {
          background: rgba(99, 102, 241, 0.1);
          color: var(--accent-primary);
        }

        .nav-icon {
          flex-shrink: 0;
        }

        .nav-label {
          margin-left: 12px;
          font-size: 14px;
          font-weight: 500;
        }

        .sidebar-footer {
          padding: 16px 8px;
          border-top: 1px solid var(--border-color);
        }
      `}</style>
    </aside>
  );
}
