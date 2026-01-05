import { cn } from "@/lib/utils";
import { useThemeStore } from "@/stores/themeStore";
import { Moon, Sun } from "lucide-react";
import { memo, useEffect } from "react";

function ThemeToggleComponent() {
  const theme = useThemeStore((s) => s.theme);
  const toggleTheme = useThemeStore((s) => s.toggleTheme);

  // Initialize theme on mount
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    // Also toggle the 'dark' class for standard tailwind dark mode if needed
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  return (
    <button
      className={cn("flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-300", "bg-secondary border border-border text-muted-foreground", "hover:bg-muted hover:text-foreground hover:scale-105 active:scale-95 shadow-sm")}
      onClick={toggleTheme}
      title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
    >
      {theme === "light" ? <Moon size={20} className="animate-in fade-in zoom-in duration-300" /> : <Sun size={20} className="animate-in fade-in zoom-in duration-300" />}
    </button>
  );
}

export const ThemeToggle = memo(ThemeToggleComponent);
