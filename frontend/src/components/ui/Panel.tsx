"use client";

import { ReactNode } from "react";

interface PanelProps {
  title?: string;
  headerAction?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, headerAction, children, className = "" }: PanelProps) {
  return (
    <div className={`panel ${className}`}>
      {title && (
        <div className="panel-header">
          <span>{title}</span>
          {headerAction}
        </div>
      )}
      <div className="panel-body">{children}</div>
    </div>
  );
}
