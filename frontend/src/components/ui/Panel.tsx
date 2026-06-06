"use client";

import { ReactNode } from "react";

interface PanelProps {
  title?: string;
  headerAction?: ReactNode;
  children: ReactNode;
  className?: string;
}

import { cn } from "@/lib/utils";

export function Panel({ title, headerAction, children, className = "" }: PanelProps) {
  return (
    <div className={cn("bg-card border border-border rounded-xl flex flex-col overflow-hidden shadow-sm", className)}>
      {title && (
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-muted/30">
          <span className="text-[13px] font-bold text-muted-foreground uppercase tracking-wider">{title}</span>
          {headerAction}
        </div>
      )}
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}
