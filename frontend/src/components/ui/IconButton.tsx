"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  tooltip?: string;
}

import { cn } from "@/lib/utils";

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(({ active = false, tooltip, className = "", children, ...props }, ref) => {
  return (
    <button
      ref={ref}
      className={cn("flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200", "text-muted-foreground hover:bg-muted hover:text-foreground active:scale-95", active ? "bg-primary/10 text-primary" : "bg-transparent", className)}
      title={tooltip}
      {...props}
    >
      {children}
    </button>
  );
});

IconButton.displayName = "IconButton";
