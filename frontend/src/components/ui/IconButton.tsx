"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  tooltip?: string;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(({ active = false, tooltip, className = "", children, ...props }, ref) => {
  const classes = ["toolbar-btn", active ? "active" : "", className].filter(Boolean).join(" ");

  return (
    <button ref={ref} className={classes} title={tooltip} {...props}>
      {children}
    </button>
  );
});

IconButton.displayName = "IconButton";
