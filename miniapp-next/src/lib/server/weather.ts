import { createServerFn } from "@tanstack/react-start";
import { cached, fetchJson } from "./cache";
import { hourlyIcon, isNightHours, weatherInfo } from "@/lib/weather/codes";

type WeatherPayload = {
  lat: number;
  lon: number;
  tz: string;
  city: string;
};

type GeoHit = {
  name: string;
  lat: number;
  lon: number;
  tz: string;
  country?: string;
  admin?: string;
};

export type WeatherHour = {
  time: string;
  temp: number;
  icon: string;
  precip: number;
};

export type WeatherNow = {
  city: string;
  temp: number;
  wind: number;
  condition: string;
  icon: string;
  hero: string;
  tone: string;
  night: boolean;
  hourly: WeatherHour[];
  ts: number;
};

type OpenMeteo = {
  current?: {
    temperature_2m: number;
    wind_speed_10m: number;
    weather_code: number;
    time: string;
  };
  hourly?: {
    time: string[];
    temperature_2m: number[];
    rain: number[];
    snowfall: number[];
    weather_code: number[];
  };
};

export const getWeather = createServerFn({ method: "GET" })
  .validator((data: WeatherPayload) => data)
  .handler(async ({ data }): Promise<WeatherNow> => {
    const lat = Number(data.lat);
    const lon = Number(data.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      throw new Error("Invalid coordinates");
    }
    const tz = encodeURIComponent(data.tz || "Europe/Moscow");
    const key = `wx:${lat.toFixed(3)},${lon.toFixed(3)}:${data.tz}`;
    return cached(key, 10 * 60_000, async () => {
      const url =
        `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
        `&current=temperature_2m,wind_speed_10m,weather_code` +
        `&hourly=temperature_2m,rain,snowfall,weather_code` +
        `&timezone=${tz}&forecast_days=2`;
      const raw = await fetchJson<OpenMeteo>(url, 8000);
      const cur = raw.current;
      if (!cur) throw new Error("Нет данных о погоде");
      const hour = new Date(cur.time).getHours();
      const night = isNightHours(hour);
      const info = weatherInfo(cur.weather_code, night);
      const hourly: WeatherHour[] = [];
      const times = raw.hourly?.time ?? [];
      const now = Date.now() - 60 * 60 * 1000;
      let start = times.findIndex((t) => new Date(t).getTime() >= now);
      if (start < 0) start = 0;
      for (let i = start; i < Math.min(start + 12, times.length); i++) {
        const t = times[i]!;
        const rain = raw.hourly?.rain[i] ?? 0;
        const snow = raw.hourly?.snowfall[i] ?? 0;
        const code = raw.hourly?.weather_code[i] ?? 0;
        const h = new Date(t).getHours();
        hourly.push({
          time: t,
          temp: Math.round(raw.hourly?.temperature_2m[i] ?? 0),
          icon: hourlyIcon(code, rain, snow, isNightHours(h)),
          precip: rain + snow,
        });
      }
      return {
        city: data.city,
        temp: Math.round(cur.temperature_2m),
        wind: Math.round(cur.wind_speed_10m * 10) / 10,
        condition: info.label,
        icon: info.icon,
        hero: info.hero,
        tone: info.tone,
        night,
        hourly,
        ts: Date.now(),
      };
    });
  });

type GeoResponse = {
  results?: {
    name: string;
    latitude: number;
    longitude: number;
    timezone?: string;
    country?: string;
    admin1?: string;
  }[];
};

export const searchCities = createServerFn({ method: "GET" })
  .validator((data: { q: string }) => data)
  .handler(async ({ data }): Promise<GeoHit[]> => {
    const q = data.q.trim().slice(0, 80);
    if (q.length < 2) return [];
    const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=6&language=ru&format=json`;
    const raw = await fetchJson<GeoResponse>(url, 6000);
    return (raw.results ?? []).map((r) => ({
      name: r.name,
      lat: r.latitude,
      lon: r.longitude,
      tz: r.timezone || "Europe/Moscow",
      country: r.country,
      admin: r.admin1,
    }));
  });
