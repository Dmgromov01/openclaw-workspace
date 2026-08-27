import { useState } from "react";
import { useSettings, verifyPin } from "@/lib/stores/settings";
import { unlockSession } from "@/lib/pin-session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { haptic } from "@/lib/haptic";

export function LockScreen({ onUnlock }: { onUnlock: () => void }) {
  const pinSalt = useSettings((s) => s.pinSalt);
  const pinHash = useSettings((s) => s.pinHash);
  const name = useSettings((s) => s.displayName);
  const [pin, setPin] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!pinSalt || !pinHash) {
      onUnlock();
      return;
    }
    setBusy(true);
    setErr("");
    const ok = await verifyPin(pin, pinSalt, pinHash);
    setBusy(false);
    if (!ok) {
      haptic("heavy");
      setErr("Неверный код");
      setPin("");
      return;
    }
    unlockSession();
    haptic("success");
    onUnlock();
  };

  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center px-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">R2D2</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">Здравствуйте{name ? `, ${name}` : ""}</h1>
      <p className="mt-2 text-sm text-muted-foreground">Введите код доступа к хабу.</p>
      <form
        className="mt-8 space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <Input
          type="password"
          inputMode="numeric"
          autoComplete="off"
          value={pin}
          onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 8))}
          placeholder="Код"
          autoFocus
        />
        {err ? <p className="text-sm font-medium text-destructive">{err}</p> : null}
        <Button className="h-12 w-full" disabled={busy || pin.length < 4}>
          Открыть
        </Button>
      </form>
    </div>
  );
}
