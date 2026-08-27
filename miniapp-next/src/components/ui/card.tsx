import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-border bg-card text-card-foreground shadow-[var(--shadow-soft)]",
        className,
      )}
      {...props}
    />
  );
}
