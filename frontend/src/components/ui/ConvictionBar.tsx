import { cn } from "@/lib/utils";

interface ConvictionBarProps {
  conviction: number;
  showLabel?: boolean;
  width?: string;
  className?: string;
}

export function ConvictionBar({ conviction, showLabel = true, width = "w-16", className }: ConvictionBarProps) {
  return (
    <div className={cn("flex items-center gap-1", className)}>
      <div className={cn("h-1.5 rounded-full bg-primary/30 overflow-hidden", width)}>
        <div
          className="h-full bg-primary rounded-full"
          style={{ width: `${conviction}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-[10px] font-bold text-muted-foreground">{conviction}</span>
      )}
    </div>
  );
}
