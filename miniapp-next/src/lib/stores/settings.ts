import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { City, HubModuleId } from "@/lib/hub/types";

export const MOSCOW: City = {
  name: "Москва",
  lat: 55.7558,
  lon: 37.6173,
  tz: "Europe/Moscow",
  country: "Россия",
};

type ThemePref = "light" | "dark" | "system";

type SettingsState = {
  displayName: string;
  onboarded: boolean;
  theme: ThemePref;
  city: City;
  enabledModules: HubModuleId[] | "all";
  pinSalt: string | null;
  pinHash: string | null;
  setDisplayName: (name: string) => void;
  setOnboarded: (v: boolean) => void;
  setTheme: (theme: ThemePref) => void;
  setCity: (city: City) => void;
  setEnabledModules: (ids: HubModuleId[] | "all") => void;
  setPin: (salt: string, hash: string) => void;
  clearPin: () => void;
  resetAll: () => void;
};

const initial = {
  displayName: "",
  onboarded: false,
  theme: "system" as ThemePref,
  city: MOSCOW,
  enabledModules: "all" as const,
  pinSalt: null as string | null,
  pinHash: null as string | null,
};

export const useSettings = create<SettingsState>()(
  persist(
    (set) => ({
      ...initial,
      setDisplayName: (displayName) => set({ displayName }),
      setOnboarded: (onboarded) => set({ onboarded }),
      setTheme: (theme) => set({ theme }),
      setCity: (city) => set({ city }),
      setEnabledModules: (enabledModules) => set({ enabledModules }),
      setPin: (pinSalt, pinHash) => set({ pinSalt, pinHash }),
      clearPin: () => set({ pinSalt: null, pinHash: null }),
      resetAll: () => set({ ...initial }),
    }),
    { name: "r2d2.settings.v1" },
  ),
);

export async function hashPin(pin: string, saltHex?: string) {
  const enc = new TextEncoder();
  const salt = saltHex
    ? Uint8Array.from(saltHex.match(/.{2}/g)!.map((b) => parseInt(b, 16)))
    : crypto.getRandomValues(new Uint8Array(16));
  const key = await crypto.subtle.importKey("raw", enc.encode(pin), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt, iterations: 120_000, hash: "SHA-256" },
    key,
    256,
  );
  const hash = [...new Uint8Array(bits)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const saltOut = [...salt].map((b) => b.toString(16).padStart(2, "0")).join("");
  return { salt: saltOut, hash };
}

export async function verifyPin(pin: string, salt: string, hash: string) {
  const next = await hashPin(pin, salt);
  if (next.hash.length !== hash.length) return false;
  let diff = 0;
  for (let i = 0; i < hash.length; i++) diff |= next.hash.charCodeAt(i) ^ hash.charCodeAt(i);
  return diff === 0;
}
