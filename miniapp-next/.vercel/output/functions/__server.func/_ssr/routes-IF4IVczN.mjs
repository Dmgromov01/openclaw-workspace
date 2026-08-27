import { i as __toESM } from "../_runtime.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { y as useNavigate } from "../_libs/@tanstack/react-router+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { t as createServerFn } from "./ssr.mjs";
import { t as useTasks } from "./tasks-CwEoy1bP.mjs";
import { C as Check, S as ChevronDown, T as Brain, _ as KeyRound, b as Coins, f as Plus, g as Languages, i as SquareCheckBig, m as Mic, o as Settings, p as Newspaper, t as X, w as CalendarDays, y as Copy } from "../_libs/lucide-react.mjs";
import { r as Header, t as AppShell } from "./header-Ba06vVxB.mjs";
import { t as createSsrRpc } from "./createSsrRpc-C1p7zOu_.mjs";
import { n as useQuery } from "../_libs/tanstack__react-query.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { d as formatTime, f as haptic, h as useSettings, i as getWeather, l as cn, n as Input, s as Button, u as formatDayLabel } from "./router-BZC-qIbN.mjs";
import { n as useCalendar, t as holidaysInRange } from "./holidays-Bms3053a.mjs";
import { t as Card } from "./card-CXjUnk0y.mjs";
import { n as ServiceRow, t as IconWell } from "./service-row-RY8e-WuZ.mjs";
import { t as Skeleton } from "./skeleton-DBbwtrCG.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/routes-IF4IVczN.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function Hourly({ data }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "no-scrollbar relative z-10 flex gap-2 overflow-x-auto px-4 pb-3 pt-1",
		children: data.hourly.map((h) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex w-11 shrink-0 flex-col items-center text-center",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "text-xs font-bold tabular-nums text-accent-foreground/95",
					children: formatTime(new Date(h.time))
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("img", {
					src: `/weather-icons/meteocons/${h.icon}.svg`,
					alt: "",
					className: "my-0.5 size-7 drop-shadow"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "text-sm font-extrabold tabular-nums",
					children: [Math.round(h.temp), "°"]
				})
			]
		}, h.time))
	});
}
function WeatherCard() {
	const city = useSettings((s) => s.city);
	const q = useQuery({
		queryKey: [
			"weather",
			city.lat,
			city.lon,
			city.tz
		],
		queryFn: () => getWeather({ data: {
			lat: city.lat,
			lon: city.lon,
			tz: city.tz,
			city: city.name
		} })
	});
	if (q.isLoading) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "mx-4 h-40 rounded-2xl" });
	if (q.isError || !q.data) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "mx-4 rounded-2xl border border-border bg-card px-4 py-6 text-center text-sm text-muted-foreground",
		children: "Погода недоступна. Проверьте сеть и город в настройках."
	});
	const w = q.data;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
		className: "weather-card mx-4",
		"data-tone": w.tone,
		style: { backgroundImage: `url(/weather-icons/hero/${w.hero})` },
		"aria-label": `Погода в ${w.city}`,
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "relative z-10 flex items-start justify-between px-4 pt-3",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "text-sm font-extrabold drop-shadow",
						children: w.city
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "text-5xl font-extrabold leading-none tracking-tight drop-shadow",
						children: [w.temp, /* @__PURE__ */ (0, import_jsx_runtime.jsx)("sup", {
							className: "text-xl font-semibold",
							children: "°C"
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "mt-0.5 text-sm font-extrabold drop-shadow",
						children: w.condition
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "text-xs font-bold text-accent-foreground/80 drop-shadow",
						children: [
							"Ветер ",
							w.wind,
							" м/с"
						]
					})
				] })
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "relative z-10 mx-4 mt-2 h-px bg-accent-foreground/25" }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Hourly, { data: w })
		]
	});
}
var getRates = createServerFn({ method: "GET" }).handler(createSsrRpc("bf54b31396212cca2300d4310fc752265d3eaaf9c42f3d6e1c78506490e2e2bf"));
function SummaryStrip() {
	const navigate = useNavigate();
	const active = useTasks((s) => s.tasks.filter((t) => !t.done).length);
	const usd = useQuery({
		queryKey: ["rates"],
		queryFn: () => getRates()
	}).data?.rates.USD;
	const pills = [
		{
			id: "tasks",
			icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SquareCheckBig, { className: "size-4" }),
			label: `${active} задач`,
			onClick: () => {
				haptic();
				document.getElementById("tasks-card")?.scrollIntoView({
					behavior: "smooth",
					block: "start"
				});
			}
		},
		{
			id: "digest",
			icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Newspaper, { className: "size-4" }),
			label: "Дайджест",
			onClick: () => {
				haptic("medium");
				navigate({ to: "/digest" });
			}
		},
		{
			id: "rates",
			icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Coins, { className: "size-4" }),
			label: usd ? `${Math.round(usd)} ₽/$` : "Курсы",
			onClick: () => {
				haptic();
				document.getElementById("rates-card")?.scrollIntoView({
					behavior: "smooth",
					block: "start"
				});
			}
		}
	];
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "no-scrollbar flex gap-2 overflow-x-auto px-4 pb-3",
		children: pills.map((p) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
			type: "button",
			onClick: p.onClick,
			className: "flex h-11 shrink-0 items-center gap-2 rounded-[18px] border border-border bg-card px-3.5 text-foreground transition-transform duration-150 active:scale-[0.98]",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(IconWell, {
				className: "size-7 border-0 bg-accent-soft text-accent",
				children: p.icon
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
				className: "text-sm font-semibold whitespace-nowrap",
				children: p.label
			})]
		}, p.id))
	});
}
var CURRENCIES = [
	"USD",
	"EUR",
	"CNY",
	"JPY",
	"GBP",
	"RUB"
];
function RatesCard() {
	const [open, setOpen] = (0, import_react.useState)(false);
	const [amount, setAmount] = (0, import_react.useState)(1e3);
	const [from, setFrom] = (0, import_react.useState)("CNY");
	const [to, setTo] = (0, import_react.useState)("RUB");
	const rates = useQuery({
		queryKey: ["rates"],
		queryFn: () => getRates()
	}).data?.rates;
	const result = (0, import_react.useMemo)(() => {
		if (!rates || !rates[from] || !rates[to]) return "—";
		return (amount * rates[from] / rates[to]).toLocaleString("ru-RU", {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		});
	}, [
		amount,
		from,
		to,
		rates
	]);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
		id: "rates-card",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
			icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Coins, { className: "size-5" }),
			title: "Валюты и конвертер",
			status: rates?.USD ? `ЦБ РФ · USD ${Math.round(rates.USD)}₽` : "Курсы ЦБ РФ",
			chevron: false,
			trailing: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChevronDown, { className: cn("size-4 text-muted-foreground transition-transform duration-200", open && "rotate-180") }),
			onClick: () => {
				haptic();
				setOpen((v) => !v);
			}
		}), open ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "space-y-2.5 border-t border-border px-4 py-3",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center gap-2",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
						type: "number",
						inputMode: "decimal",
						value: amount,
						onChange: (e) => setAmount(Number(e.target.value)),
						className: "min-w-0 flex-1 font-bold tabular-nums"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
						value: from,
						onChange: (e) => setFrom(e.target.value),
						className: "h-11 rounded-xl border border-border bg-muted px-2 text-xs font-bold text-foreground",
						children: CURRENCIES.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
							value: c,
							children: c
						}, c))
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "text-muted-foreground",
						children: "→"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
						value: to,
						onChange: (e) => setTo(e.target.value),
						className: "h-11 rounded-xl border border-border bg-muted px-2 text-xs font-bold text-foreground",
						children: CURRENCIES.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
							value: c,
							children: c
						}, c))
					})
				]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between rounded-xl border border-success/25 bg-success/10 px-3.5 py-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "text-xs font-bold uppercase tracking-wide text-muted-foreground",
					children: "Результат"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
					className: "text-base font-extrabold tabular-nums text-success",
					children: [
						result,
						" ",
						to
					]
				})]
			})]
		}) : null]
	});
}
function formatCreated(ts) {
	return new Date(ts).toLocaleString("ru-RU", {
		day: "2-digit",
		month: "2-digit",
		hour: "2-digit",
		minute: "2-digit"
	});
}
function TasksCard() {
	const navigate = useNavigate();
	const { tasks, add, toggle, remove } = useTasks();
	const [value, setValue] = (0, import_react.useState)("");
	const [voiceError, setVoiceError] = (0, import_react.useState)("");
	const active = tasks.filter((t) => !t.done);
	const done = tasks.filter((t) => t.done);
	const submit = (text) => {
		add(text ?? value);
		setValue("");
		haptic("medium");
	};
	const startVoice = () => {
		const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
		if (!SR) {
			setVoiceError("Голосовой ввод не поддерживается");
			setTimeout(() => setVoiceError(""), 2500);
			return;
		}
		const rec = new SR();
		rec.lang = "ru-RU";
		rec.interimResults = false;
		rec.onresult = (e) => {
			setValue(e.results[0]?.[0]?.transcript ?? "");
		};
		rec.onerror = () => {
			setVoiceError("Не удалось распознать речь");
			setTimeout(() => setVoiceError(""), 2500);
		};
		rec.start();
		haptic("medium");
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
		id: "tasks-card",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
			accent: true,
			icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SquareCheckBig, { className: "size-5" }),
			title: "Задачи",
			status: `${active.length} активных · ${done.length} в архиве`,
			onClick: () => {
				haptic();
				navigate({ to: "/archive" });
			}
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "space-y-2 border-t border-border px-4 py-3",
			children: [
				active.slice(0, 6).map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-3 rounded-xl border border-border bg-muted p-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
							type: "button",
							onClick: () => {
								haptic();
								toggle(t.id);
							},
							className: cn("flex size-6 shrink-0 items-center justify-center rounded-lg border-2 border-border-strong bg-card", t.done && "border-accent bg-accent text-accent-foreground"),
							"aria-label": t.done ? "Вернуть" : "Выполнить",
							children: t.done ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "text-xs font-black",
								children: "✓"
							}) : null
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "min-w-0 flex-1",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "text-xs font-medium tabular-nums text-muted-foreground",
								children: formatCreated(t.createdAt)
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "text-sm font-semibold leading-snug text-foreground",
								children: t.text
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
							type: "button",
							onClick: () => {
								haptic();
								remove(t.id);
							},
							className: "grid size-9 place-items-center text-muted-foreground hover:text-destructive",
							"aria-label": "Удалить",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "size-4" })
						})
					]
				}, t.id)),
				active.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "py-3 text-center text-xs text-muted-foreground",
					children: "Все дела выполнены. Добавьте новую задачу."
				}) : null,
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex gap-2 pt-1",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							placeholder: "Новая задача…",
							value,
							onChange: (e) => setValue(e.target.value),
							onKeyDown: (e) => {
								if (e.key === "Enter") submit();
							},
							className: "flex-1"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "button",
							variant: "secondary",
							size: "icon",
							onClick: startVoice,
							"aria-label": "Надиктовать",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Mic, { className: "size-4" })
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "button",
							variant: "solid",
							size: "icon",
							onClick: () => submit(),
							"aria-label": "Добавить",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Plus, { className: "size-4" })
						})
					]
				}),
				voiceError ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "text-xs font-semibold text-destructive",
					children: voiceError
				}) : null
			]
		})]
	});
}
function upcomingDays(n) {
	const start = /* @__PURE__ */ new Date();
	start.setHours(0, 0, 0, 0);
	return Array.from({ length: n }, (_, i) => {
		const d = new Date(start);
		d.setDate(start.getDate() + i);
		return d;
	});
}
function CalendarCard() {
	const navigate = useNavigate();
	const events = useCalendar((s) => s.events);
	const add = useCalendar((s) => s.add);
	const [draft, setDraft] = (0, import_react.useState)("");
	const [when, setWhen] = (0, import_react.useState)("");
	const visible = (0, import_react.useMemo)(() => {
		const list = upcomingDays(7);
		const from = list[0].toISOString();
		const to = new Date(list[6].getTime() + 864e5).toISOString();
		const holidays = holidaysInRange(from, to);
		const all = [...events, ...holidays];
		return list.map((d) => {
			const key = d.toISOString().slice(0, 10);
			const dayEvents = all.filter((e) => e.start.slice(0, 10) === key).sort((a, b) => a.start.localeCompare(b.start));
			return {
				date: d,
				key,
				label: formatDayLabel(d),
				events: dayEvents
			};
		});
	}, [events]).filter((d) => d.events.length > 0);
	const addQuick = () => {
		const summary = draft.trim();
		if (!summary) return;
		const start = when || new Date(Date.now() + 36e5).toISOString().slice(0, 16);
		add({
			start: new Date(start).toISOString(),
			summary
		});
		setDraft("");
		haptic("medium");
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
		icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CalendarDays, { className: "size-5" }),
		title: "Календарь",
		status: "7 дней · локальные события и праздники",
		onClick: () => {
			haptic();
			navigate({ to: "/calendar" });
		}
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-2 border-t border-border px-4 py-3",
		children: [visible.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "py-2 text-center text-xs text-muted-foreground",
			children: "На ближайшие 7 дней событий нет."
		}) : visible.map((d) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "rounded-xl border border-border bg-muted p-3",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mb-1.5 text-xs font-bold uppercase tracking-wide text-muted-foreground",
				children: d.label
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "space-y-1.5",
				children: d.events.map((ev) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-start gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "mt-0.5 shrink-0 font-mono text-xs font-extrabold tabular-nums text-accent",
						children: ev.allDay ? "весь день" : ev.start.slice(11, 16)
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "min-w-0 flex-1 text-sm font-semibold leading-snug",
						children: ev.summary
					})]
				}, ev.id))
			})]
		}, d.key)), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex gap-2 pt-1",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
					placeholder: "Новое событие…",
					value: draft,
					onChange: (e) => setDraft(e.target.value),
					onKeyDown: (e) => {
						if (e.key === "Enter") addQuick();
					}
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
					type: "datetime-local",
					value: when,
					onChange: (e) => setWhen(e.target.value),
					className: "h-11 w-[9.5rem] rounded-xl border border-border bg-muted px-2 text-xs text-foreground",
					"aria-label": "Дата и время"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					type: "button",
					variant: "solid",
					size: "icon",
					onClick: addQuick,
					"aria-label": "Добавить событие",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Plus, { className: "size-4" })
				})
			]
		})]
	})] });
}
var LOWER = "abcdefghijkmnopqrstuvwxyz";
var UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ";
var NUM = "23456789";
var SYM = "!@#$%^&*_+-=";
function pick(chars, n) {
	const out = [];
	const buf = new Uint32Array(n);
	crypto.getRandomValues(buf);
	for (let i = 0; i < n; i++) out.push(chars[buf[i] % chars.length]);
	return out;
}
function shuffle(items) {
	const buf = new Uint32Array(items.length);
	crypto.getRandomValues(buf);
	for (let i = items.length - 1; i > 0; i--) {
		const j = buf[i] % (i + 1);
		[items[i], items[j]] = [items[j], items[i]];
	}
	return items;
}
function generatePassword(opts) {
	const length = Math.min(64, Math.max(8, Math.round(opts.length)));
	const pools = [LOWER];
	if (opts.upper) pools.push(UPPER);
	if (opts.numbers) pools.push(NUM);
	if (opts.symbols) pools.push(SYM);
	const all = pools.join("");
	const required = pools.map((p) => pick(p, 1)[0]);
	const rest = pick(all, Math.max(0, length - required.length));
	return shuffle([...required, ...rest]).join("");
}
function passwordStrength(pw) {
	let score = 0;
	if (pw.length >= 12) score += 1;
	if (pw.length >= 16) score += 1;
	if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score += 1;
	if (/\d/.test(pw)) score += 1;
	if (/[^A-Za-z0-9]/.test(pw)) score += 1;
	if (score <= 2) return {
		label: "слабый",
		level: 1
	};
	if (score <= 3) return {
		label: "средний",
		level: 2
	};
	return {
		label: "надёжный",
		level: 3
	};
}
function PasswordCard() {
	const [open, setOpen] = (0, import_react.useState)(false);
	const [length, setLength] = (0, import_react.useState)(16);
	const [symbols, setSymbols] = (0, import_react.useState)(true);
	const [password, setPassword] = (0, import_react.useState)(() => generatePassword({
		length: 16,
		upper: true,
		numbers: true,
		symbols: true
	}));
	const [copied, setCopied] = (0, import_react.useState)(false);
	const strength = passwordStrength(password);
	const regen = () => {
		haptic();
		setPassword(generatePassword({
			length,
			upper: true,
			numbers: true,
			symbols
		}));
		setCopied(false);
	};
	const copy = async () => {
		await navigator.clipboard.writeText(password);
		setCopied(true);
		haptic("success");
		toast("Скопировано");
		setTimeout(() => setCopied(false), 1600);
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
		icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(KeyRound, { className: "size-5" }),
		title: "Пароли",
		status: "Криптостойкий генератор",
		chevron: false,
		trailing: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "text-sm text-muted-foreground",
			children: open ? "▲" : "▼"
		}),
		onClick: () => {
			haptic();
			setOpen((v) => !v);
		}
	}), open ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3 border-t border-border px-4 py-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
				type: "range",
				min: 12,
				max: 32,
				value: length,
				onChange: (e) => {
					const n = Number(e.target.value);
					setLength(n);
					setPassword(generatePassword({
						length: n,
						upper: true,
						numbers: true,
						symbols
					}));
				},
				className: "w-full accent-[var(--accent)]"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between text-xs font-bold text-accent",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
					className: "font-mono tabular-nums",
					children: [length, " симв."]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: cn(strength.level === 1 && "text-destructive", strength.level === 2 && "text-warning", strength.level === 3 && "text-success"),
					children: strength.label
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
				className: "flex items-center gap-2 text-sm text-muted-foreground",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
					type: "checkbox",
					checked: symbols,
					onChange: (e) => setSymbols(e.target.checked)
				}), "Спецсимволы"]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
				type: "button",
				onClick: copy,
				className: "flex w-full items-center justify-between gap-2 rounded-xl border border-dashed border-border-strong bg-muted p-3.5 text-left",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "break-all font-mono text-xs font-bold",
					children: password
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "shrink-0 text-xs font-bold text-accent",
					children: copied ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Check, { className: "size-4" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Copy, { className: "size-4" })
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
				variant: "solid",
				className: "w-full",
				onClick: regen,
				children: "Сгенерировать новый"
			})
		]
	}) : null] });
}
function HomeView() {
	const navigate = useNavigate();
	const name = useSettings((s) => s.displayName);
	const enabled = useSettings((s) => s.enabledModules);
	const show = (id) => enabled === "all" || enabled.includes(id);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AppShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header, {
		title: "R2D2",
		subtitle: name ? `Привет, ${name}` : "мини-приложение",
		right: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
			variant: "secondary",
			size: "icon-sm",
			"aria-label": "Настройки",
			onClick: () => {
				haptic();
				navigate({ to: "/settings" });
			},
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Settings, { className: "size-4" })
		})
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SummaryStrip, {}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(WeatherCard, {}),
			show("rates") ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "px-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(RatesCard, {})
			}) : null,
			show("tasks") ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "px-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TasksCard, {})
			}) : null,
			show("calendar") ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "px-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CalendarCard, {})
			}) : null,
			show("passwords") ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "px-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(PasswordCard, {})
			}) : null,
			show("fun") ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "px-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Card, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
					icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Brain, { className: "size-5" }),
					title: "Викторины и идеи",
					status: "Вопросы и чем заняться",
					onClick: () => {
						haptic("medium");
						navigate({ to: "/fun" });
					}
				}) })
			}) : null,
			show("translate") ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "px-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Card, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
					icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Languages, { className: "size-5" }),
					title: "Переводчик и словарь",
					status: "EN · ES · RU",
					onClick: () => {
						haptic("medium");
						navigate({ to: "/translate" });
					}
				}) })
			}) : null
		]
	})] });
}
var SplitComponent = HomeView;
//#endregion
export { SplitComponent as component };
