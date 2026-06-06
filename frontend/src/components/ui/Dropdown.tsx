"use client";

import { cn } from "@/lib/utils";
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
    <div ref={ref} className={cn("relative inline-block", className)}>
      <div className="cursor-pointer" onClick={() => setIsOpen(!isOpen)}>
        {trigger}
      </div>
      {isOpen && (
        <div
          className={cn("absolute z-50 mt-1 min-w-[max-content]", align === "right" ? "right-0" : "left-0")}
          onClick={(e) => {
            // Close on any click inside by default, unless handled
            if (!e.defaultPrevented) setIsOpen(false);
          }}
        >
          {children}
        </div>
      )}
    </div>
  );
}

interface DropdownItemProps {
  children: ReactNode;
  active?: boolean;
  onClick?: (e: React.MouseEvent) => void;
  className?: string;
}

export function DropdownItem({ children, active = false, onClick, className = "" }: DropdownItemProps) {
  return (
    <div
      className={cn("px-4 py-2 text-sm cursor-pointer transition-colors", active ? "bg-primary/10 text-primary font-bold" : "text-foreground hover:bg-muted", className)}
      onClick={(e) => {
        if (onClick) {
          onClick(e);
        }
      }}
    >
      {children}
    </div>
  );
}

export function DropdownDivider() {
  return <div className="h-px bg-border my-1" />;
}
