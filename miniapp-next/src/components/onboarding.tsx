import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { searchCities } from "@/lib/server/weather";
import { MOSCOW, useSettings } from "@/lib/stores/settings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { haptic } from "@/lib/haptic";
import type { City } from "@/lib/hub/types";

export function Onboarding() {
  const setDisplayName = useSettings((s) => s.setDisplayName);
  const setCity = useSettings((s) => s.setCity);
  const setOnboarded = useSettings((s) => s.setOnboarded);
  const [name, setName] = useState("");
  const [query, setQuery] = useState("Москва");
  const [city, setLocalCity] = useState<City>(MOSCOW);
  const search = useMutation({
    mutationFn: (q: string) => searchCities({ data: { q } }),
  });

  const finish = () => {
    const n = name.trim().slice(0, 40) || "Гость";
    setDisplayName(n);
    setCity(city);
    setOnboarded(true);
    haptic("success");
  };

  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center px-6 py-10">
      <div className="enter">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Personal hub</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight text-foreground">R2D2</h1>
        <p className="mt-2 max-w-sm text-sm leading-relaxed text-muted-foreground">
          Погода, курсы, задачи, дайджест и переводчик — в одном спокойном экране.
        </p>
      </div>
      <div className="enter enter-2 mt-8 space-y-3">
        <label className="block text-xs font-semibold text-muted-foreground">Как к вам обращаться</label>
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Имя" autoFocus />
        <label className="block pt-2 text-xs font-semibold text-muted-foreground">Город для погоды</label>
        <div className="flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") search.mutate(query);
            }}
            placeholder="Найти город"
          />
          <Button type="button" variant="secondary" onClick={() => search.mutate(query)}>
            Найти
          </Button>
        </div>
        <div className="space-y-1">
          <button
            type="button"
            onClick={() => {
              setLocalCity(MOSCOW);
              setQuery(MOSCOW.name);
            }}
            className="w-full rounded-xl border border-border bg-card px-3 py-2.5 text-left text-sm font-medium"
          >
            {city.name === MOSCOW.name ? "Выбрано: " : ""}
            Москва
          </button>
          {(search.data ?? []).map((c) => (
            <button
              key={`${c.lat}-${c.lon}`}
              type="button"
              onClick={() => {
                setLocalCity({
                  name: c.name,
                  lat: c.lat,
                  lon: c.lon,
                  tz: c.tz,
                  country: c.country,
                });
                setQuery(c.name);
              }}
              className="w-full rounded-xl border border-border bg-muted px-3 py-2.5 text-left text-sm"
            >
              {c.name}
              {c.admin ? `, ${c.admin}` : ""}
              {c.country ? ` · ${c.country}` : ""}
            </button>
          ))}
        </div>
      </div>
      <Button className="enter enter-3 mt-8 h-12 w-full" onClick={finish}>
        Продолжить
      </Button>
    </div>
  );
}
