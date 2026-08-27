import { useEffect, useState, type ReactNode } from "react";
import { useSettings } from "@/lib/stores/settings";
import { isSessionUnlocked } from "@/lib/pin-session";
import { Onboarding } from "./onboarding";
import { LockScreen } from "./lock-screen";

export function Gate({ children }: { children: ReactNode }) {
  const onboarded = useSettings((s) => s.onboarded);
  const pinHash = useSettings((s) => s.pinHash);
  const [unlocked, setUnlocked] = useState(true);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const finish = () => {
      const hash = useSettings.getState().pinHash;
      setUnlocked(!hash || isSessionUnlocked());
      setReady(true);
    };
    if (useSettings.persist.hasHydrated()) finish();
    const unsub = useSettings.persist.onFinishHydration(finish);
    return unsub;
  }, [pinHash]);

  if (!ready) {
    return <div className="min-h-dvh bg-background" />;
  }
  if (!onboarded) return <Onboarding />;
  if (pinHash && !unlocked) return <LockScreen onUnlock={() => setUnlocked(true)} />;
  return children;
}
