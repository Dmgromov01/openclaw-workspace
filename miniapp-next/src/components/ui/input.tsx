import * as React from "react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "flex h-11 w-full rounded-xl border border-border bg-muted px-3.5 text-sm text-foreground outline-none transition-[box-shadow,border-color] duration-150 placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring/50",
        className,
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex min-h-24 w-full resize-none rounded-xl border border-border bg-muted p-3.5 text-sm text-foreground outline-none transition-[box-shadow,border-color] duration-150 placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring/50",
        className,
      )}
      {...props}
    />
  );
}
