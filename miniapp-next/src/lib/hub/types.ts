import type { LucideIcon } from "lucide-react";

export type HubModuleId =
  | "home"
  | "digest"
  | "fun"
  | "translate"
  | "tasks"
  | "calendar"
  | "rates"
  | "passwords"
  | "settings";

export type HubModule = {
  id: HubModuleId;
  title: string;
  shortTitle: string;
  description: string;
  icon: LucideIcon;
  path: string;
  showInTabBar: boolean;
  showOnHome: boolean;
  order: number;
};

export type HubUser = {
  displayName: string;
  source: "local" | "telegram";
  telegramId?: number;
  role: "owner" | "admin" | "user";
};

export type AuthAdapter = {
  kind: "none" | "telegram" | "session";
  getUser: () => HubUser | null;
};

export type City = {
  name: string;
  lat: number;
  lon: number;
  tz: string;
  country?: string;
};

export type DigestSourceType = "rss" | "tg";

export type DigestSource = {
  id: string;
  type: DigestSourceType;
  name: string;
  title: string;
  enabled: boolean;
};

export type TaskItem = {
  id: string;
  text: string;
  done: boolean;
  createdAt: number;
};

export type DictEntry = {
  id: string;
  src: string;
  dst: string;
  pair: string;
  createdAt: number;
};

export type CalEvent = {
  id: string;
  start: string;
  end?: string;
  summary: string;
  location?: string;
  source: "local" | "holiday" | "google";
  allDay?: boolean;
};

export type CalendarProvider = {
  id: string;
  label: string;
  readonly: boolean;
  fetchRange: (fromIso: string, toIso: string) => Promise<CalEvent[]>;
  create?: (event: Omit<CalEvent, "id" | "source">) => Promise<CalEvent>;
  remove?: (id: string) => Promise<void>;
};
