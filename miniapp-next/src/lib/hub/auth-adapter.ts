import type { AuthAdapter, HubUser } from "./types";

/**
 * Auth is a plug-in, not a hard dependency.
 *
 * - `localAdapter` — preview / personal device (no accounts).
 * - `telegramAdapter` — Telegram Mini App initData (wire later).
 * - `sessionAdapter` — cookie/session backend (wire later).
 *
 * Keep user-owned data in local stores until a real identity is attached.
 */
function readLocalUser(): HubUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("r2d2.settings.v1");
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { state?: { displayName?: string } };
    const name = parsed.state?.displayName?.trim();
    if (!name) return null;
    return {
      displayName: name,
      source: "local",
      role: "owner",
    };
  } catch {
    return null;
  }
}

export const localAdapter: AuthAdapter = {
  kind: "none",
  getUser: readLocalUser,
};

export const authAdapter: AuthAdapter = localAdapter;

export function currentUser() {
  return authAdapter.getUser();
}
