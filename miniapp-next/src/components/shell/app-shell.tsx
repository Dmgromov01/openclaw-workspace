import type { ReactNode } from "react";
import { TabBar } from "./tab-bar";
import { cn } from "@/lib/utils";

export function AppShell({
  children,
  withTabs = true,
  className,
}: {
  children: ReactNode;
  withTabs?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mx-auto min-h-dvh w-full max-w-lg bg-background",
        withTabs && "pb-[calc(86px+env(safe-area-inset-bottom))]",
        className,
      )}
    >
      {children}
      {withTabs ? <TabBar /> : null}
    </div>
  );
}
