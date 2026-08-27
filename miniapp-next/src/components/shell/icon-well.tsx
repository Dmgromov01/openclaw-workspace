import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function IconWell({
  children,
  accent = false,
  className,
}: {
  children: ReactNode;
  accent?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex size-10 shrink-0 items-center justify-center rounded-full border",
        accent
          ? "border-transparent bg-accent-soft text-accent"
          : "border-border bg-muted text-foreground",
        className,
      )}
    >
      {children}
    </div>
  );
}
