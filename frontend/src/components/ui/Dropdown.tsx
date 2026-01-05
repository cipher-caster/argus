"use client";

import { ChevronDown } from "lucide-react";
import { ReactNode, useEffect, useRef, useState } from "react";

interface DropdownProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: "left" | "right";
  className?: string;
}

export function Dropdown({ trigger, children, align = "left", className = "" }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={ref} className={`dropdown ${className}`}>
      <div className="dropdown-trigger" onClick={() => setIsOpen(!isOpen)}>
        {trigger}
        <ChevronDown size={14} style={{ opacity: 0.6 }} />
      </div>
      {isOpen && <div className={`dropdown-menu ${align === "right" ? "dropdown-menu-right" : ""}`}>{children}</div>}
    </div>
  );
}

interface DropdownItemProps {
  children: ReactNode;
  active?: boolean;
  onClick?: () => void;
}

export function DropdownItem({ children, active = false, onClick }: DropdownItemProps) {
  return (
    <div className={`dropdown-item ${active ? "active" : ""}`} onClick={onClick}>
      {children}
    </div>
  );
}

export function DropdownDivider() {
  return <div className="dropdown-divider" />;
}
