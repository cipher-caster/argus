import { useThemeStore } from "@/stores/themeStore";
import { Moon, Sun } from "lucide-react";
import { memo, useEffect } from "react";

function ThemeToggleComponent() {
  const theme = useThemeStore((s) => s.theme);
  const toggleTheme = useThemeStore((s) => s.toggleTheme);
  const setTheme = useThemeStore((s) => s.setTheme);

  // Initialize theme on mount
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  return (
    <button className="theme-toggle" onClick={toggleTheme} title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}>
      {theme === "light" ? (
        // Moon icon for switching to dark
        <Moon size={20} />
      ) : (
        // Sun icon for switching to light
        <Sun size={20} />
      )}

      <style jsx>{`
        .theme-toggle {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .theme-toggle:hover {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }
      `}</style>
    </button>
  );
}

export const ThemeToggle = memo(ThemeToggleComponent);
