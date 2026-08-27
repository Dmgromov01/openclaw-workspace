import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Mic, Plus, SquareCheckBig, X } from "lucide-react";
import { useTasks } from "@/lib/stores/tasks";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ServiceRow } from "@/components/shell/service-row";
import { haptic } from "@/lib/haptic";
import { cn } from "@/lib/utils";

function formatCreated(ts: number) {
  return new Date(ts).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function TasksCard() {
  const navigate = useNavigate();
  const { tasks, add, toggle, remove } = useTasks();
  const [value, setValue] = useState("");
  const [voiceError, setVoiceError] = useState("");
  const active = tasks.filter((t) => !t.done);
  const done = tasks.filter((t) => t.done);

  const submit = (text?: string) => {
    add(text ?? value);
    setValue("");
    haptic("medium");
  };

  const startVoice = () => {
    const SR =
      (window as unknown as { SpeechRecognition?: new () => SpeechRecognition }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: new () => SpeechRecognition }).webkitSpeechRecognition;
    if (!SR) {
      setVoiceError("Голосовой ввод не поддерживается");
      setTimeout(() => setVoiceError(""), 2500);
      return;
    }
    const rec = new SR();
    rec.lang = "ru-RU";
    rec.interimResults = false;
    rec.onresult = (e: SpeechRecognitionEvent) => {
      setValue(e.results[0]?.[0]?.transcript ?? "");
    };
    rec.onerror = () => {
      setVoiceError("Не удалось распознать речь");
      setTimeout(() => setVoiceError(""), 2500);
    };
    rec.start();
    haptic("medium");
  };

  return (
    <Card id="tasks-card">
      <ServiceRow
        accent
        icon={<SquareCheckBig className="size-5" />}
        title="Задачи"
        status={`${active.length} активных · ${done.length} в архиве`}
        onClick={() => {
          haptic();
          navigate({ to: "/archive" });
        }}
      />
      <div className="space-y-2 border-t border-border px-4 py-3">
        {active.slice(0, 6).map((t) => (
          <div key={t.id} className="flex items-center gap-3 rounded-xl border border-border bg-muted p-3">
            <button
              type="button"
              onClick={() => {
                haptic();
                toggle(t.id);
              }}
              className={cn(
                "flex size-6 shrink-0 items-center justify-center rounded-lg border-2 border-border-strong bg-card",
                t.done && "border-accent bg-accent text-accent-foreground",
              )}
              aria-label={t.done ? "Вернуть" : "Выполнить"}
            >
              {t.done ? <span className="text-xs font-black">✓</span> : null}
            </button>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium tabular-nums text-muted-foreground">{formatCreated(t.createdAt)}</div>
              <div className="text-sm font-semibold leading-snug text-foreground">{t.text}</div>
            </div>
            <button
              type="button"
              onClick={() => {
                haptic();
                remove(t.id);
              }}
              className="grid size-9 place-items-center text-muted-foreground hover:text-destructive"
              aria-label="Удалить"
            >
              <X className="size-4" />
            </button>
          </div>
        ))}
        {active.length === 0 ? (
          <div className="py-3 text-center text-xs text-muted-foreground">Все дела выполнены. Добавьте новую задачу.</div>
        ) : null}
        <div className="flex gap-2 pt-1">
          <Input
            placeholder="Новая задача…"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
            className="flex-1"
          />
          <Button type="button" variant="secondary" size="icon" onClick={startVoice} aria-label="Надиктовать">
            <Mic className="size-4" />
          </Button>
          <Button type="button" variant="solid" size="icon" onClick={() => submit()} aria-label="Добавить">
            <Plus className="size-4" />
          </Button>
        </div>
        {voiceError ? <div className="text-xs font-semibold text-destructive">{voiceError}</div> : null}
      </div>
    </Card>
  );
}

type SpeechRecognition = {
  lang: string;
  interimResults: boolean;
  onresult: ((e: SpeechRecognitionEvent) => void) | null;
  onerror: (() => void) | null;
  start: () => void;
};
type SpeechRecognitionEvent = { results: { 0?: { 0?: { transcript: string } } } };
