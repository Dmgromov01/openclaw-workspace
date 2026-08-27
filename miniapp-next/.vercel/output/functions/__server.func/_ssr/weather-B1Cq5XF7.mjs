import { t as createServerFn } from "./ssr.mjs";
import { t as createServerRpc } from "./createServerRpc-A6pJPYTF.mjs";
import { n as fetchJson, t as cached } from "./cache-DQJ8TyLZ.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/weather-B1Cq5XF7.js
var TABLE = {
	0: {
		label: "Ясно",
		day: "clear-day",
		night: "clear-night",
		hero: "sunny-hero.png",
		tone: "clear"
	},
	1: {
		label: "Почти ясно",
		day: "partly-cloudy-day",
		night: "partly-cloudy-night",
		hero: "mostly-sunny-hero.png",
		tone: "clear"
	},
	2: {
		label: "Переменная облачность",
		day: "partly-cloudy-day",
		night: "partly-cloudy-night",
		hero: "partly-cloudy-hero.png",
		tone: "cloud"
	},
	3: {
		label: "Пасмурно",
		day: "overcast",
		night: "overcast-night",
		hero: "overcast-hero.png",
		tone: "cloud"
	},
	45: {
		label: "Туман",
		day: "fog",
		night: "fog-night",
		hero: "fog-hero.png",
		tone: "fog"
	},
	48: {
		label: "Изморозь",
		day: "fog",
		night: "fog-night",
		hero: "fog-hero.png",
		tone: "fog"
	},
	51: {
		label: "Морось",
		day: "drizzle",
		night: "drizzle",
		hero: "drizzle-hero.png",
		tone: "rain"
	},
	53: {
		label: "Морось",
		day: "drizzle",
		night: "drizzle",
		hero: "drizzle-hero.png",
		tone: "rain"
	},
	55: {
		label: "Сильная морось",
		day: "drizzle",
		night: "drizzle",
		hero: "drizzle-hero.png",
		tone: "rain"
	},
	61: {
		label: "Небольшой дождь",
		day: "rain",
		night: "rain",
		hero: "rain-hero.png",
		tone: "rain"
	},
	63: {
		label: "Дождь",
		day: "rain",
		night: "rain",
		hero: "rain-hero.png",
		tone: "rain"
	},
	65: {
		label: "Сильный дождь",
		day: "rain",
		night: "rain",
		hero: "heavy-rain-hero.png",
		tone: "rain"
	},
	71: {
		label: "Небольшой снег",
		day: "snow",
		night: "snow",
		hero: "light-snow-hero.png",
		tone: "snow"
	},
	73: {
		label: "Снег",
		day: "snow",
		night: "snow",
		hero: "snow-hero.png",
		tone: "snow"
	},
	75: {
		label: "Сильный снег",
		day: "snow",
		night: "snow",
		hero: "snow-hero.png",
		tone: "snow"
	},
	77: {
		label: "Снежные зёрна",
		day: "snow",
		night: "snow",
		hero: "sleet-hero.png",
		tone: "snow"
	},
	80: {
		label: "Ливень",
		day: "rain",
		night: "rain",
		hero: "rain-hero.png",
		tone: "rain"
	},
	81: {
		label: "Ливень",
		day: "rain",
		night: "rain",
		hero: "heavy-rain-hero.png",
		tone: "rain"
	},
	82: {
		label: "Сильный ливень",
		day: "thunderstorms",
		night: "thunderstorms",
		hero: "thunderstorm-hero.png",
		tone: "storm"
	},
	85: {
		label: "Снегопад",
		day: "snow",
		night: "snow",
		hero: "snow-hero.png",
		tone: "snow"
	},
	86: {
		label: "Сильный снегопад",
		day: "snow",
		night: "snow",
		hero: "snow-hero.png",
		tone: "snow"
	},
	95: {
		label: "Гроза",
		day: "thunderstorms",
		night: "thunderstorms",
		hero: "thunderstorm-hero.png",
		tone: "storm"
	},
	96: {
		label: "Гроза с градом",
		day: "thunderstorms",
		night: "thunderstorms",
		hero: "thunderstorm-hero.png",
		tone: "storm"
	},
	99: {
		label: "Гроза с градом",
		day: "thunderstorms",
		night: "thunderstorms",
		hero: "thunderstorm-hero.png",
		tone: "storm"
	}
};
function isNightHours(hour) {
	return hour >= 21 || hour < 6;
}
function weatherInfo(code, night) {
	const row = TABLE[code] ?? TABLE[2];
	return {
		label: row.label,
		icon: night ? row.night : row.day,
		hero: row.hero,
		tone: row.tone
	};
}
function hourlyIcon(code, rain, snow, night) {
	const precip = rain + snow;
	if (precip > 0) {
		if (snow >= rain && snow > 0) return "snow";
		if (precip < .3) return "drizzle";
		if (precip < 3) return "rain";
		return code >= 95 ? "thunderstorms" : "rain";
	}
	return weatherInfo(code, night).icon;
}
var getWeather_createServerFn_handler = createServerRpc({
	id: "7cf7d5e69bcb3ccff5d1b5139f463568a2ca48ece792ed1d28515bda49861864",
	name: "getWeather",
	filename: "src/lib/server/weather.ts"
}, (opts) => getWeather.__executeServer(opts));
var getWeather = createServerFn({ method: "GET" }).validator((data) => data).handler(getWeather_createServerFn_handler, async ({ data }) => {
	const lat = Number(data.lat);
	const lon = Number(data.lon);
	if (!Number.isFinite(lat) || !Number.isFinite(lon)) throw new Error("Invalid coordinates");
	const tz = encodeURIComponent(data.tz || "Europe/Moscow");
	const key = `wx:${lat.toFixed(3)},${lon.toFixed(3)}:${data.tz}`;
	return cached(key, 6e5, async () => {
		const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,wind_speed_10m,weather_code&hourly=temperature_2m,rain,snowfall,weather_code&timezone=${tz}&forecast_days=2`;
		const raw = await fetchJson(url, 8e3);
		const cur = raw.current;
		if (!cur) throw new Error("Нет данных о погоде");
		const night = isNightHours(new Date(cur.time).getHours());
		const info = weatherInfo(cur.weather_code, night);
		const hourly = [];
		const times = raw.hourly?.time ?? [];
		const now = Date.now() - 36e5;
		let start = times.findIndex((t) => new Date(t).getTime() >= now);
		if (start < 0) start = 0;
		for (let i = start; i < Math.min(start + 12, times.length); i++) {
			const t = times[i];
			const rain = raw.hourly?.rain[i] ?? 0;
			const snow = raw.hourly?.snowfall[i] ?? 0;
			const code = raw.hourly?.weather_code[i] ?? 0;
			const h = new Date(t).getHours();
			hourly.push({
				time: t,
				temp: Math.round(raw.hourly?.temperature_2m[i] ?? 0),
				icon: hourlyIcon(code, rain, snow, isNightHours(h)),
				precip: rain + snow
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
			ts: Date.now()
		};
	});
});
var searchCities_createServerFn_handler = createServerRpc({
	id: "828bedc192e156c67e34471d374a4df5027fff3e4f3d0156db94b97d15318830",
	name: "searchCities",
	filename: "src/lib/server/weather.ts"
}, (opts) => searchCities.__executeServer(opts));
var searchCities = createServerFn({ method: "GET" }).validator((data) => data).handler(searchCities_createServerFn_handler, async ({ data }) => {
	const q = data.q.trim().slice(0, 80);
	if (q.length < 2) return [];
	const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=6&language=ru&format=json`;
	return ((await fetchJson(url, 6e3)).results ?? []).map((r) => ({
		name: r.name,
		lat: r.latitude,
		lon: r.longitude,
		tz: r.timezone || "Europe/Moscow",
		country: r.country,
		admin: r.admin1
	}));
});
//#endregion
export { getWeather_createServerFn_handler, searchCities_createServerFn_handler };
