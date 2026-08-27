import { useState } from "react";
import { Rss, Send, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useSources } from "@/lib/stores/sources";
import { AppShell } from "@/components/shell/app-shell";
import { Header } from "@/components/shell/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ServiceRow } from "@/components/shell/service-row";
import { haptic } from "@/lib/haptic";
import { cn } from "@/lib/utils";
import type { DigestSourceType } from "@/lib/hub/types";

export function SourcesView() {
  const { sources, add, remove, toggle } = useSources();
  const [type, setType] = useState<DigestSourceType>("rss");
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");

  const submit = () => {
    const err = add({ type, name, title: title || name });
    if (err) {
      toast(err);
      return;
    }
    setName("");
    setTitle("");
    haptic("medium");
    toast("Источник подключён");
  };

  return (
    <AppShell>
      <Header title="Источники" subtitle="Каналы и RSS для дайджеста" backTo="/digest" />
      <div className="space-y-3 px-4">
        <Card>
          {sources.map((s, i) => (
            <div key={s.id} className={i > 0 ? "border-t border-border" : ""}>
              <ServiceRow
                icon={s.type === "tg" ? <Send className="size-5" /> : <Rss className="size-5" />}
                title={s.title}
                status={s.enabled ? (s.type === "tg" ? "Telegram · отключён парсер" : "RSS") : "выключен"}
                chevron={false}
                onClick={() => toggle(s.id)}
                trailing={
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      haptic();
                      remove(s.id);
                    }}
                    className="grid size-9 place-items-center rounded-xl bg-muted text-muted-foreground"
                    aria-label="Удалить"
                  >
                    <Trash2 className="size-4" />
                  </button>
                }
              />
            </div>
          ))}
        </Card>

        <Card className="space-y-3 p-4">
          <div className="flex gap-1.5 rounded-xl bg-muted p-1.5">
            {(
              [
                { id: "rss" as const, label: "RSS" },
                { id: "tg" as const, label: "Telegram" },
              ]
            ).map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setType(t.id)}
                className={cn(
                  "h-10 flex-1 rounded-lg text-xs font-bold",
                  type === t.id ? "bg-accent text-accent-foreground" : "text-muted-foreground",
                )}
              >
                {t.label}
              </button>
            ))}
          </div>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={type === "tg" ? "@channel или t.me/…" : "https://site.com/rss"}
          />
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Название (необязательно)" />
          <Button className="w-full" onClick={submit}>
            Подключить источник
          </Button>
          {type === "tg" ? (
            <p className="text-xs leading-relaxed text-muted-foreground">
              Telegram-каналы зарезервированы в архитектуре. Сейчас дайджест читает HTTPS RSS — укажите ленту
              издания, если она есть.
            </p>
          ) : null}
        </Card>
      </div>
    </AppShell>
  );
}
