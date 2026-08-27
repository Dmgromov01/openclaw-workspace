import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { searchCities } from "@/lib/server/weather";
import { hashPin, MOSCOW, useSettings } from "@/lib/stores/settings";
import { lockSession } from "@/lib/pin-session";
import { AppShell } from "@/components/shell/app-shell";
import { Header } from "@/components/shell/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { haptic } from "@/lib/haptic";
import { HUB_MODULES } from "@/lib/hub/registry";
import type { HubModuleId } from "@/lib/hub/types";

export function SettingsView() {
  const s = useSettings();
  const [name, setName] = useState(s.displayName);
  const [q, setQ] = useState(s.city.name);
  const [pin, setPin] = useState("");
  const search = useMutation({
    mutationFn: (query: string) => searchCities({ data: { q: query } }),
  });

  const saveName = () => {
    s.setDisplayName(name.trim().slice(0, 40) || "Гость");
    haptic("success");
    toast("Имя сохранено");
  };

  const setTheme = (theme: "light" | "dark" | "system") => {
    s.setTheme(theme);
    haptic();
  };

  const toggleModule = (id: HubModuleId) => {
    const current = s.enabledModules === "all" ? HUB_MODULES.map((m) => m.id) : [...s.enabledModules];
    const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
    const core: HubModuleId[] = ["home", "settings"];
    const merged = Array.from(new Set([...core, ...next]));
    s.setEnabledModules(merged.length >= HUB_MODULES.length ? "all" : merged);
    haptic();
  };

  const enabled = (id: HubModuleId) => s.enabledModules === "all" || s.enabledModules.includes(id);

  return (
    <AppShell>
      <Header title="Настройки" subtitle="Профиль и модули" backTo="/" />
      <div className="space-y-3 px-4">
        <Card className="space-y-3 p-4">
          <div className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Профиль</div>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Имя" />
          <Button variant="secondary" onClick={saveName}>
            Сохранить имя
          </Button>
        </Card>

        <Card className="space-y-3 p-4">
          <div className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Тема</div>
          <div className="grid grid-cols-3 gap-1.5 rounded-xl bg-muted p-1.5">
            {(["light", "dark", "system"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTheme(t)}
                className={`h-10 rounded-lg text-xs font-bold ${
                  s.theme === t ? "bg-accent text-accent-foreground" : "text-muted-foreground"
                }`}
              >
                {t === "light" ? "Светлая" : t === "dark" ? "Тёмная" : "Система"}
              </button>
            ))}
          </div>
        </Card>

        <Card className="space-y-3 p-4">
          <div className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Город</div>
          <div className="flex gap-2">
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Найти город" />
            <Button variant="secondary" onClick={() => search.mutate(q)}>
              Найти
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">Сейчас: {s.city.name}</p>
          <button
            type="button"
            className="w-full rounded-xl bg-muted px-3 py-2 text-left text-sm"
            onClick={() => {
              s.setCity(MOSCOW);
              setQ(MOSCOW.name);
            }}
          >
            Москва
          </button>
          {(search.data ?? []).map((c) => (
            <button
              key={`${c.lat}-${c.lon}`}
              type="button"
              className="w-full rounded-xl bg-muted px-3 py-2 text-left text-sm"
              onClick={() => {
                s.setCity({ name: c.name, lat: c.lat, lon: c.lon, tz: c.tz, country: c.country });
                setQ(c.name);
                toast("Город обновлён");
              }}
            >
              {c.name}
              {c.admin ? `, ${c.admin}` : ""}
            </button>
          ))}
        </Card>

        <Card className="space-y-3 p-4">
          <div className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Код доступа</div>
          <p className="text-sm text-muted-foreground">
            Локальный PIN на этом устройстве. Не уходит на сервер.
          </p>
          <Input
            type="password"
            inputMode="numeric"
            value={pin}
            onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 8))}
            placeholder="4–8 цифр"
          />
          <div className="flex gap-2">
            <Button
              className="flex-1"
              disabled={pin.length < 4}
              onClick={async () => {
                const { salt, hash } = await hashPin(pin);
                s.setPin(salt, hash);
                setPin("");
                toast("Код установлен");
              }}
            >
              Установить
            </Button>
            {s.pinHash ? (
              <Button
                variant="outline"
                onClick={() => {
                  s.clearPin();
                  toast("Код снят");
                }}
              >
                Снять
              </Button>
            ) : null}
          </div>
          {s.pinHash ? (
            <Button
              variant="secondary"
              onClick={() => {
                lockSession();
                window.location.reload();
              }}
            >
              Заблокировать сейчас
            </Button>
          ) : null}
        </Card>

        <Card className="space-y-1 p-4">
          <div className="mb-2 text-xs font-bold uppercase tracking-wide text-muted-foreground">Модули</div>
          {HUB_MODULES.filter((m) => m.id !== "home" && m.id !== "settings").map((m) => (
            <div key={m.id} className="flex items-center justify-between gap-3 py-2">
              <div>
                <div className="text-sm font-semibold">{m.title}</div>
                <div className="text-xs text-muted-foreground">{m.description}</div>
              </div>
              <Switch checked={enabled(m.id)} onCheckedChange={() => toggleModule(m.id)} />
            </div>
          ))}
        </Card>
      </div>
    </AppShell>
  );
}
