import { useState } from "react";
import { Check, Copy, KeyRound } from "lucide-react";
import { toast } from "sonner";
import { generatePassword, passwordStrength } from "@/lib/password";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ServiceRow } from "@/components/shell/service-row";
import { haptic } from "@/lib/haptic";
import { cn } from "@/lib/utils";

export function PasswordCard() {
  const [open, setOpen] = useState(false);
  const [length, setLength] = useState(16);
  const [symbols, setSymbols] = useState(true);
  const [password, setPassword] = useState(() => generatePassword({ length: 16, upper: true, numbers: true, symbols: true }));
  const [copied, setCopied] = useState(false);
  const strength = passwordStrength(password);

  const regen = () => {
    haptic();
    setPassword(generatePassword({ length, upper: true, numbers: true, symbols }));
    setCopied(false);
  };

  const copy = async () => {
    await navigator.clipboard.writeText(password);
    setCopied(true);
    haptic("success");
    toast("Скопировано");
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <Card>
      <ServiceRow
        icon={<KeyRound className="size-5" />}
        title="Пароли"
        status="Криптостойкий генератор"
        chevron={false}
        trailing={
          <span className="text-sm text-muted-foreground">{open ? "▲" : "▼"}</span>
        }
        onClick={() => {
          haptic();
          setOpen((v) => !v);
        }}
      />
      {open ? (
        <div className="space-y-3 border-t border-border px-4 py-3">
          <input
            type="range"
            min={12}
            max={32}
            value={length}
            onChange={(e) => {
              const n = Number(e.target.value);
              setLength(n);
              setPassword(generatePassword({ length: n, upper: true, numbers: true, symbols }));
            }}
            className="w-full accent-[var(--accent)]"
          />
          <div className="flex items-center justify-between text-xs font-bold text-accent">
            <span className="font-mono tabular-nums">{length} симв.</span>
            <span
              className={cn(
                strength.level === 1 && "text-destructive",
                strength.level === 2 && "text-warning",
                strength.level === 3 && "text-success",
              )}
            >
              {strength.label}
            </span>
          </div>
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input type="checkbox" checked={symbols} onChange={(e) => setSymbols(e.target.checked)} />
            Спецсимволы
          </label>
          <button
            type="button"
            onClick={copy}
            className="flex w-full items-center justify-between gap-2 rounded-xl border border-dashed border-border-strong bg-muted p-3.5 text-left"
          >
            <span className="break-all font-mono text-xs font-bold">{password}</span>
            <span className="shrink-0 text-xs font-bold text-accent">
              {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
            </span>
          </button>
          <Button variant="solid" className="w-full" onClick={regen}>
            Сгенерировать новый
          </Button>
        </div>
      ) : null}
    </Card>
  );
}
