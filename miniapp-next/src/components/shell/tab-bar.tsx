import { Link, useRouterState } from "@tanstack/react-router";
import { tabModules } from "@/lib/hub/registry";
import { useSettings } from "@/lib/stores/settings";
import { haptic } from "@/lib/haptic";
import { cn } from "@/lib/utils";

export function TabBar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const enabled = useSettings((s) => s.enabledModules);
  const tabs = tabModules(enabled);

  return (
    <nav
      className="tabbar fixed inset-x-0 bottom-0 z-30 flex h-[74px] items-center justify-around border-t border-border bg-card"
      aria-label="Основная навигация"
    >
      {tabs.map((tab) => {
        const active = tab.path === "/" ? pathname === "/" : pathname.startsWith(tab.path);
        const Icon = tab.icon;
        return (
          <Link
            key={tab.id}
            to={tab.path}
            onClick={() => haptic()}
            className="flex min-h-11 min-w-14 flex-col items-center justify-center gap-0.5"
            aria-current={active ? "page" : undefined}
          >
            <Icon
              className={cn("size-5", active ? "text-accent" : "text-muted-foreground")}
              strokeWidth={active ? 2.2 : 1.8}
            />
            <span
              className={cn(
                "text-[10px] font-medium",
                active ? "text-accent" : "text-muted-foreground",
              )}
            >
              {tab.shortTitle}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
