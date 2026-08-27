import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Badge({
  className,
  tone = "muted",
  children,
}: {
  className?: string;
  tone?: "muted" | "accent" | "success" | "warning";
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-lg px-2 py-0.5 text-xs font-semibold",
        tone === "muted" && "bg-muted text-muted-foreground",
        tone === "accent" && "bg-accent-soft text-accent",
        tone === "success" && "bg-success/10 text-success",
        tone === "warning" && "bg-warning/15 text-warning",
        className,
      )}
    >
      {children}
    </span>
  );
}
