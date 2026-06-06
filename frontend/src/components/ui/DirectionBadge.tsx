import { cn } from "@/lib/utils";

interface DirectionBadgeProps {
  direction: "LONG" | "SHORT";
  className?: string;
  size?: "sm" | "md";
}

export function DirectionBadge({ direction, className, size = "sm" }: DirectionBadgeProps) {
  const isLong = direction === "LONG";
  return (
    <span className={cn(
      "font-black rounded uppercase tracking-wide",
      size === "sm" ? "text-[9px] px-1.5 py-0.5" : "text-[10px] px-2 py-0.5",
      isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500",
      className
    )}>
      {direction}
    </span>
  );
}
