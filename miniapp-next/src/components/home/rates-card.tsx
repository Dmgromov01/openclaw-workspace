import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, Coins } from "lucide-react";
import { getRates } from "@/lib/server/rates";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ServiceRow } from "@/components/shell/service-row";
import { haptic } from "@/lib/haptic";
import { cn } from "@/lib/utils";

const CURRENCIES = ["USD", "EUR", "CNY", "JPY", "GBP", "RUB"] as const;

export function RatesCard() {
  const [open, setOpen] = useState(false);
  const [amount, setAmount] = useState(1000);
  const [from, setFrom] = useState("CNY");
  const [to, setTo] = useState("RUB");
  const q = useQuery({ queryKey: ["rates"], queryFn: () => getRates() });
  const rates = q.data?.rates;

  const result = useMemo(() => {
    if (!rates || !rates[from] || !rates[to]) return "—";
    const rub = amount * rates[from]!;
    const out = rub / rates[to]!;
    return out.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }, [amount, from, to, rates]);

  return (
    <Card id="rates-card">
      <ServiceRow
        icon={<Coins className="size-5" />}
        title="Валюты и конвертер"
        status={rates?.USD ? `ЦБ РФ · USD ${Math.round(rates.USD)}₽` : "Курсы ЦБ РФ"}
        chevron={false}
        trailing={
          <ChevronDown
            className={cn("size-4 text-muted-foreground transition-transform duration-200", open && "rotate-180")}
          />
        }
        onClick={() => {
          haptic();
          setOpen((v) => !v);
        }}
      />
      {open ? (
        <div className="space-y-2.5 border-t border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <Input
              type="number"
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="min-w-0 flex-1 font-bold tabular-nums"
            />
            <select
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="h-11 rounded-xl border border-border bg-muted px-2 text-xs font-bold text-foreground"
            >
              {CURRENCIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <span className="text-muted-foreground">→</span>
            <select
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="h-11 rounded-xl border border-border bg-muted px-2 text-xs font-bold text-foreground"
            >
              {CURRENCIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center justify-between rounded-xl border border-success/25 bg-success/10 px-3.5 py-3">
            <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Результат</span>
            <span className="text-base font-extrabold tabular-nums text-success">
              {result} {to}
            </span>
          </div>
        </div>
      ) : null}
    </Card>
  );
}
