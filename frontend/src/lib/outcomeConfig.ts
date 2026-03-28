/**
 * Unified outcome configuration for WIN/LOSS/OPEN/REVIEW/REJECTED mappings.
 */

export interface OutcomeConfig {
  label: string;
  emoji: string;
  cls: string;
}

export const OUTCOME_CONFIG: Record<string, OutcomeConfig> = {
  WIN:      { label: "WIN",      emoji: "✅", cls: "text-emerald-500 dark:text-emerald-400 bg-emerald-500/10" },
  LOSS:     { label: "LOSS",     emoji: "❌", cls: "text-red-500 dark:text-red-400 bg-red-500/10" },
  REVIEW:   { label: "REVIEW",   emoji: "👀", cls: "text-amber-500 dark:text-amber-400 bg-amber-500/10" },
  OPEN:     { label: "OPEN",     emoji: "🔄", cls: "text-sky-500 dark:text-sky-400 bg-sky-500/10" },
  REJECTED: { label: "REJECTED", emoji: "🚫", cls: "text-zinc-500 dark:text-zinc-400 bg-zinc-500/10" },
} as const;

export const OUTCOME_STYLE: Record<string, string> = {
  WIN: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
  LOSS: "text-red-500 bg-red-500/10 border-red-500/20",
  REVIEW: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  OPEN: "text-sky-500 bg-sky-500/10 border-sky-500/20",
  REJECTED: "text-zinc-500 bg-zinc-500/10 border-zinc-500/20",
};

export const OUTCOME_EMOJI: Record<string, string> = {
  WIN: "✅",
  LOSS: "❌",
  REVIEW: "👀",
  OPEN: "🔄",
  REJECTED: "🚫",
};
