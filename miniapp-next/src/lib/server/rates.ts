import { createServerFn } from "@tanstack/react-start";
import { cached, fetchJson } from "./cache";

export type RatesMap = Record<string, number>;

type Cbr = {
  Valute?: Record<string, { Value: number; Nominal: number }>;
};

export const getRates = createServerFn({ method: "GET" }).handler(async (): Promise<{ rates: RatesMap; ts: number }> => {
  return cached("cbr-rates", 30 * 60_000, async () => {
    const raw = await fetchJson<Cbr>("https://www.cbr-xml-daily.ru/daily_json.js", 8000);
    const v = raw.Valute ?? {};
    const pick = (code: string) => {
      const row = v[code];
      if (!row) return 0;
      return row.Value / (row.Nominal || 1);
    };
    return {
      rates: {
        USD: pick("USD"),
        EUR: pick("EUR"),
        CNY: pick("CNY"),
        JPY: pick("JPY"),
        GBP: pick("GBP"),
        RUB: 1,
      },
      ts: Date.now(),
    };
  });
});
