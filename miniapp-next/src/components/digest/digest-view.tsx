import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Radio, RefreshCw, Rss, ScanText } from "lucide-react";
import { getDigest } from "@/lib/server/digest";
import { summarizeDigest } from "@/lib/server/ai";
import { useSources } from "@/lib/stores/sources";
import { AppShell } from "@/components/shell/app-shell";
import { Header } from "@/components/shell/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ServiceRow } from "@/components/shell/service-row";
import { Skeleton } from "@/components/ui/skeleton";
import { haptic } from "@/lib/haptic";

export function DigestView() {
  const navigate = useNavigate();
  const sources = useSources((s) => s.sources.filter((x) => x.enabled));
  const [open, setOpen] = useState<Record<number, boolean>>({});
  const [summaries, setSummaries] = useState<Record<number, string>>({});

  const q = useQuery({
    queryKey: ["digest", sources.map((s) => s.id).join(",")],
    queryFn: () =>
      getDigest({
        data: {
          sources: sources.map((s) => ({ type: s.type, name: s.name, title: s.title })),
        },
      }),
  });

  const sum = useMutation({
    mutationFn: (i: number) => {
      const block = q.data?.blocks[i];
      if (!block) return Promise.resolve({ text: "" });
      return summarizeDigest({
        data: { title: block.title, posts: block.posts.map((p) => p.text) },
      });
    },
    onSuccess: (res, i) => {
      if (res.unavailable) {
        setSummaries((s) => ({ ...s, [i]: "AI-саммари сейчас недоступно." }));
        return;
      }
      if (res.text) setSummaries((s) => ({ ...s, [i]: res.text }));
    },
  });

  return (
    <AppShell>
      <Header
        title="Дайджест"
        subtitle={`${sources.length} источников`}
        backTo="/"
        right={
          <Button
            variant="secondary"
            size="icon-sm"
            aria-label="Обновить"
            onClick={() => {
              haptic("light");
              void q.refetch();
            }}
          >
            <RefreshCw className="size-4" />
          </Button>
        }
      />
      <div className="space-y-3 px-4">
        <Card>
          <ServiceRow
            icon={<Radio className="size-5" />}
            title="Источники"
            status={`${sources.length} подключено · RSS`}
            onClick={() => {
              haptic();
              navigate({ to: "/sources" });
            }}
          />
        </Card>

        {q.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-36" />
            <Skeleton className="h-36" />
          </div>
        ) : null}
        {q.isError ? (
          <p className="py-8 text-center text-sm text-destructive">Не удалось собрать дайджест.</p>
        ) : null}
        {q.data?.blocks.map((block, i) => (
          <Card key={block.title + i}>
            <ServiceRow
              icon={<Rss className="size-5" />}
              title={block.title}
              status={block.error ? block.error : `${block.posts.length} материалов`}
              chevron={false}
            />
            <div className="space-y-2.5 border-t border-border px-4 py-3">
              {summaries[i] ? (
                <p className="text-sm leading-relaxed text-foreground">{summaries[i]}</p>
              ) : null}
              {open[i]
                ? block.posts.map((p, pi) => (
                    <div
                      key={pi}
                      className="rounded-xl bg-muted px-3 py-2 text-xs leading-relaxed text-muted-foreground"
                    >
                      {p.text}
                    </div>
                  ))
                : null}
              {block.posts.length > 0 ? (
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    className="flex-1"
                    onClick={() => {
                      haptic("light");
                      setOpen((s) => ({ ...s, [i]: !s[i] }));
                    }}
                  >
                    {open[i] ? "Скрыть" : `Показать (${block.posts.length})`}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      haptic("medium");
                      sum.mutate(i);
                    }}
                    disabled={sum.isPending}
                  >
                    <ScanText className="size-4" />
                    Саммари
                  </Button>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">{block.error || "Свежих материалов нет."}</p>
              )}
            </div>
          </Card>
        ))}
        {q.data && q.data.blocks.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">Добавьте источники, чтобы собрать ленту.</p>
        ) : null}
      </div>
    </AppShell>
  );
}
