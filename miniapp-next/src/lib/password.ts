export type PasswordOptions = {
  length: number;
  upper: boolean;
  numbers: boolean;
  symbols: boolean;
};

const LOWER = "abcdefghijkmnopqrstuvwxyz";
const UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ";
const NUM = "23456789";
const SYM = "!@#$%^&*_+-=";

function pick(chars: string, n: number) {
  const out: string[] = [];
  const buf = new Uint32Array(n);
  crypto.getRandomValues(buf);
  for (let i = 0; i < n; i++) out.push(chars[buf[i]! % chars.length]!);
  return out;
}

function shuffle(items: string[]) {
  const buf = new Uint32Array(items.length);
  crypto.getRandomValues(buf);
  for (let i = items.length - 1; i > 0; i--) {
    const j = buf[i]! % (i + 1);
    [items[i], items[j]] = [items[j]!, items[i]!];
  }
  return items;
}

export function generatePassword(opts: PasswordOptions) {
  const length = Math.min(64, Math.max(8, Math.round(opts.length)));
  const pools = [LOWER];
  if (opts.upper) pools.push(UPPER);
  if (opts.numbers) pools.push(NUM);
  if (opts.symbols) pools.push(SYM);
  const all = pools.join("");
  const required = pools.map((p) => pick(p, 1)[0]!);
  const rest = pick(all, Math.max(0, length - required.length));
  return shuffle([...required, ...rest]).join("");
}

export function passwordStrength(pw: string) {
  let score = 0;
  if (pw.length >= 12) score += 1;
  if (pw.length >= 16) score += 1;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score += 1;
  if (/\d/.test(pw)) score += 1;
  if (/[^A-Za-z0-9]/.test(pw)) score += 1;
  if (score <= 2) return { label: "слабый", level: 1 as const };
  if (score <= 3) return { label: "средний", level: 2 as const };
  return { label: "надёжный", level: 3 as const };
}
