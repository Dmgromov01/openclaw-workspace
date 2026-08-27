const KEY = "r2d2.unlocked";

export function isSessionUnlocked() {
  if (typeof window === "undefined") return true;
  return sessionStorage.getItem(KEY) === "1";
}

export function unlockSession() {
  sessionStorage.setItem(KEY, "1");
}

export function lockSession() {
  sessionStorage.removeItem(KEY);
}
