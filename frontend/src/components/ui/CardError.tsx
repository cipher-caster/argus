import { WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";

export function CardError({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2 text-[11px] text-muted-foreground/50 font-medium", className)}>
      <WifiOff size={12} />
      Failed to load — backend may be offline
    </div>
  );
}
