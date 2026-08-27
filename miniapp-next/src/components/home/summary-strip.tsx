import { useNavigate } from "@tanstack/react-router";
import { Coins, Newspaper, SquareCheckBig } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getRates } from "@/lib/server/rates";
import { useTasks } from "@/lib/stores/tasks";
import { haptic } from "@/lib/haptic";
import { IconWell } from "@/components/shell/icon-well";

export function SummaryStrip() {
  const navigate = useNavigate();
  const active = useTasks((s) => s.tasks.filter((t) => !t.done).length);
  const rates = useQuery({ queryKey: ["rates"], queryFn: () => getRates() });
  const usd = rates.data?.rates.USD;

  const pills = [
    {
      id: "tasks",
      icon: <SquareCheckBig className="size-4" />,
      label: `${active} задач`,
      onClick: () => {
        haptic();
        document.getElementById("tasks-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
      },
    },
    {
      id: "digest",
      icon: <Newspaper className="size-4" />,
      label: "Дайджест",
      onClick: () => {
        haptic("medium");
        navigate({ to: "/digest" });
      },
    },
    {
      id: "rates",
      icon: <Coins className="size-4" />,
      label: usd ? `${Math.round(usd)} ₽/$` : "Курсы",
      onClick: () => {
        haptic();
        document.getElementById("rates-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
      },
    },
  ];

  return (
    <div className="no-scrollbar flex gap-2 overflow-x-auto px-4 pb-3">
      {pills.map((p) => (
        <button
          key={p.id}
          type="button"
          onClick={p.onClick}
          className="flex h-11 shrink-0 items-center gap-2 rounded-[18px] border border-border bg-card px-3.5 text-foreground transition-transform duration-150 active:scale-[0.98]"
        >
          <IconWell className="size-7 border-0 bg-accent-soft text-accent">{p.icon}</IconWell>
          <span className="text-sm font-semibold whitespace-nowrap">{p.label}</span>
        </button>
      ))}
    </div>
  );
}
