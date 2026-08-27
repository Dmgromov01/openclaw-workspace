import { useQuery } from "@tanstack/react-query";
import { getWeather, type WeatherNow } from "@/lib/server/weather";
import { useSettings } from "@/lib/stores/settings";
import { Skeleton } from "@/components/ui/skeleton";
import { formatTime } from "@/lib/utils";

function Hourly({ data }: { data: WeatherNow }) {
  return (
    <div className="no-scrollbar relative z-10 flex gap-2 overflow-x-auto px-4 pb-3 pt-1">
      {data.hourly.map((h) => (
        <div key={h.time} className="flex w-11 shrink-0 flex-col items-center text-center">
          <div className="text-xs font-bold tabular-nums text-accent-foreground/95">
            {formatTime(new Date(h.time))}
          </div>
          <img
            src={`/weather-icons/meteocons/${h.icon}.svg`}
            alt=""
            className="my-0.5 size-7 drop-shadow"
          />
          <div className="text-sm font-extrabold tabular-nums">{Math.round(h.temp)}°</div>
        </div>
      ))}
    </div>
  );
}

export function WeatherCard() {
  const city = useSettings((s) => s.city);
  const q = useQuery({
    queryKey: ["weather", city.lat, city.lon, city.tz],
    queryFn: () =>
      getWeather({ data: { lat: city.lat, lon: city.lon, tz: city.tz, city: city.name } }),
  });

  if (q.isLoading) {
    return <Skeleton className="mx-4 h-40 rounded-2xl" />;
  }
  if (q.isError || !q.data) {
    return (
      <div className="mx-4 rounded-2xl border border-border bg-card px-4 py-6 text-center text-sm text-muted-foreground">
        Погода недоступна. Проверьте сеть и город в настройках.
      </div>
    );
  }

  const w = q.data;
  return (
    <section
      className="weather-card mx-4"
      data-tone={w.tone}
      style={{
        backgroundImage: `url(/weather-icons/hero/${w.hero})`,
      }}
      aria-label={`Погода в ${w.city}`}
    >
      <div className="relative z-10 flex items-start justify-between px-4 pt-3">
        <div>
          <div className="text-sm font-extrabold drop-shadow">{w.city}</div>
          <div className="text-5xl font-extrabold leading-none tracking-tight drop-shadow">
            {w.temp}
            <sup className="text-xl font-semibold">°C</sup>
          </div>
          <div className="mt-0.5 text-sm font-extrabold drop-shadow">{w.condition}</div>
          <div className="text-xs font-bold text-accent-foreground/80 drop-shadow">Ветер {w.wind} м/с</div>
        </div>
      </div>
      <div className="relative z-10 mx-4 mt-2 h-px bg-accent-foreground/25" />
      <Hourly data={w} />
    </section>
  );
}
