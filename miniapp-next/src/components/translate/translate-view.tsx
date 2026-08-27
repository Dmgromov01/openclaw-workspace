import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Trash2, X } from "lucide-react";
import { toast } from "sonner";
import { translateText } from "@/lib/server/translate";
import { useDictionary } from "@/lib/stores/dictionary";
import { AppShell } from "@/components/shell/app-shell";
import { Header } from "@/components/shell/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { haptic } from "@/lib/haptic";
import { cn } from "@/lib/utils";

const PAIRS = [
  { id: "en|ru", label: "EN → RU" },
  { id: "ru|en", label: "RU → EN" },
  { id: "es|ru", label: "ES → RU" },
  { id: "ru|es", label: "RU → ES" },
];

export function TranslateView() {
  const { entries, add, remove } = useDictionary();
  const [pair, setPair] = useState("en|ru");
  const [text, setText] = useState("");
  const [result, setResult] = useState("");
  const [src, setSrc] = useState("");
  const [dst, setDst] = useState("");

  const tr = useMutation({
    mutationFn: () => translateText({ data: { text, pair } }),
    onSuccess: (d) => setResult(d.text),
    onError: (e) => toast(e instanceof Error ? e.message : "Ошибка перевода"),
  });

  return (
    <AppShell>
      <Header
        title="Переводчик"
        subtitle="Английский, испанский, русский"
        backTo="/"
        right={
          <Button
            variant="secondary"
            size="icon-sm"
            aria-label="Очистить"
            onClick={() => {
              setText("");
              setResult("");
            }}
          >
            <Trash2 className="size-4" />
          </Button>
        }
      />
      <div className="space-y-3 px-4">
        <Card className="flex gap-1 p-1.5">
          {PAIRS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => {
                haptic("light");
                setPair(p.id);
                setResult("");
              }}
              className={cn(
                "h-10 flex-1 rounded-xl text-xs font-bold transition-colors duration-150",
                pair === p.id ? "bg-accent text-accent-foreground" : "text-muted-foreground",
              )}
            >
              {p.label}
            </button>
          ))}
        </Card>

        <Card className="space-y-3 p-4">
          <Textarea
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value.slice(0, 1500))}
            placeholder="Вставьте текст для перевода…"
          />
          <div className="flex gap-2">
            <Button
              className="flex-1"
              disabled={tr.isPending || !text.trim()}
              onClick={() => {
                haptic("medium");
                tr.mutate();
              }}
            >
              {tr.isPending ? "…" : "Перевести"}
            </Button>
            <Button
              variant="secondary"
              size="icon"
              onClick={() => {
                setText("");
                setResult("");
              }}
            >
              <X className="size-4" />
            </Button>
          </div>
          {result ? (
            <div className="space-y-2 rounded-xl border border-success/25 bg-success/10 p-3.5">
              <p className="whitespace-pre-wrap break-words text-sm">{result}</p>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    void navigator.clipboard.writeText(result);
                    haptic("success");
                    toast("Скопировано");
                  }}
                >
                  Копировать
                </Button>
                <Button
                  size="sm"
                  variant="solid"
                  className="flex-1"
                  onClick={() => {
                    add(text, result, pair);
                    haptic("medium");
                    toast("В словаре");
                  }}
                >
                  В словарь
                </Button>
              </div>
            </div>
          ) : null}
        </Card>

        <Card className="space-y-3 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
              Словарь ({entries.length})
            </span>
            <span className="text-xs text-muted-foreground">на этом устройстве</span>
          </div>
          <Input value={src} onChange={(e) => setSrc(e.target.value)} placeholder="Фраза…" />
          <Input value={dst} onChange={(e) => setDst(e.target.value)} placeholder="Перевод…" />
          <Button
            variant="solid"
            className="w-full"
            disabled={!src.trim()}
            onClick={() => {
              add(src, dst, pair);
              setSrc("");
              setDst("");
              haptic("medium");
            }}
          >
            Добавить в словарь
          </Button>
          {entries.length === 0 ? (
            <p className="rounded-xl bg-muted px-3 py-4 text-center text-xs text-muted-foreground">
              Словарь пуст. Сохраните перевод или добавьте пару вручную.
            </p>
          ) : (
            <div className="max-h-72 space-y-2 overflow-y-auto">
              {entries.map((x) => (
                <div key={x.id} className="rounded-xl border border-border bg-muted px-3 py-2.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-sm font-bold break-words">{x.src}</div>
                    <button
                      type="button"
                      onClick={() => {
                        haptic("light");
                        remove(x.id);
                      }}
                      className="grid size-8 place-items-center text-muted-foreground"
                      aria-label="Удалить"
                    >
                      <X className="size-4" />
                    </button>
                  </div>
                  {x.dst ? <div className="text-xs text-muted-foreground">{x.dst}</div> : null}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </AppShell>
  );
}
