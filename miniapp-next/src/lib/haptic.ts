type HapticKind = "light" | "medium" | "heavy" | "success";

export function haptic(kind: HapticKind = "light") {
  try {
    const tg = (
      window as unknown as {
        Telegram?: {
          WebApp?: {
            HapticFeedback?: {
              impactOccurred: (k: string) => void;
              notificationOccurred: (k: string) => void;
            };
          };
        };
      }
    ).Telegram?.WebApp?.HapticFeedback;
    if (tg) {
      if (kind === "success") tg.notificationOccurred("success");
      else tg.impactOccurred(kind);
      return;
    }
  } catch {
    /* ignore */
  }
  if (typeof navigator !== "undefined" && "vibrate" in navigator) {
    const ms = kind === "heavy" ? 24 : kind === "medium" ? 16 : kind === "success" ? 12 : 8;
    navigator.vibrate(ms);
  }
}
